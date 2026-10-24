"""Authenticated, narrowly scoped cleanup for the n8n Telegram video wizard.
No model loading, subprocesses, extra packages or writable Docker output mount.
"""
import hmac
import json
import os
from pathlib import Path
import re
import secrets

from aiohttp import web
import folder_paths
from server import PromptServer

# This is the SAME Windows directory mounted as /files inside n8n.
SHARED_MEDIA_ROOT = Path(r"E:\AI\media")
STATE_ROOT = SHARED_MEDIA_ROOT / '.telegram-ui'
STATE_ROOT.mkdir(parents=True, exist_ok=True)
KEY_FILE = STATE_ROOT / 'comfy-control.key'
try:
    with KEY_FILE.open('x', encoding='ascii') as stream:
        stream.write(secrets.token_hex(32))
        stream.flush()
        os.fsync(stream.fileno())
except FileExistsError:
    pass
try:
    os.chmod(KEY_FILE, 0o600)
except OSError:
    pass


def _regular_tree(path, root):
    """Plan all files before deleting any; reject symlinks and Windows junctions."""
    if not path.exists() and not path.is_symlink():
        return [], []
    if path.is_symlink() or (hasattr(path, 'is_junction') and path.is_junction()):
        raise ValueError('Links/junctions are not permitted')
    if not path.resolve().is_relative_to(root.resolve()):
        raise ValueError('Path escapes allowed root')
    if path.is_file():
        return [path], []
    if not path.is_dir():
        raise ValueError('Not a regular file/directory')
    files, directories = [], []
    for child in path.iterdir():
        f, d = _regular_tree(child, root)
        files.extend(f)
        directories.extend(d)
    directories.append(path)
    return files, directories


def delete_job(request_id):
    if not isinstance(request_id, str) or not re.fullmatch(r'tg-0-[0-9]+', request_id):
        raise ValueError('Invalid request_id')
    registry = STATE_ROOT / 'scheduler' / 'jobs' / (request_id + '.json')
    record = json.loads(registry.read_text(encoding='utf-8'))
    if record.get('request_id') != request_id or record.get('status') != 'deleting' or record.get('inflight'):
        raise ValueError('Job must be reserved for deletion by n8n')
    running, pending = PromptServer.instance.prompt_queue.get_current_queue()
    if running or pending:
        raise ValueError('Wait for ComfyUI to be idle before deleting')
    output_root = Path(folder_paths.get_output_directory()).resolve()
    parent = output_root / 'video' / 'n8n'
    # Check every ancestor before enumerating, including an existing video/n8n junction.
    for p in [output_root / 'video', parent]:
        if p.is_symlink() or (hasattr(p, 'is_junction') and p.is_junction()):
            raise ValueError('Linked output directory is not permitted')
    folders = []
    if parent.exists():
        folders = [p for p in parent.iterdir() if p.name == request_id or re.fullmatch(re.escape(request_id)+r'-e[0-9]+', p.name)]
    files, directories = [], []
    for p in folders:
        f, d = _regular_tree(p, output_root)
        files.extend(f)
        directories.extend(d)
    # ComfyUI uploads have a unique request-id prefix. Never delete unrelated inputs.
    input_root = Path(folder_paths.get_input_directory()).resolve()
    upload_name = record.get('request', {}).get('upload_name', '')
    image = record.get('request', {}).get('image', '')
    if upload_name and upload_name != request_id + '_' + image and not (upload_name == image and Path(image).stem == request_id and re.fullmatch(r'[A-Za-z0-9_-]+\.(?:png|jpe?g|webp)', image, re.I)):
        raise ValueError('Unexpected uploaded image name')
    if upload_name:
        stem = Path(upload_name).stem
        suffix = Path(upload_name).suffix
        for p in input_root.iterdir():
            if p.name == upload_name or re.fullmatch(re.escape(stem)+r' \([0-9]+\)'+re.escape(suffix), p.name):
                if not p.is_file() or p.is_symlink():
                    raise ValueError('Linked input is not permitted')
                files.append(p)
    count = 0
    for p in files:
        p.unlink(missing_ok=True)
        count += 1
    for p in directories:
        p.rmdir()
    return {'ok': True, 'request_id': request_id, 'removed_files': count}


@PromptServer.instance.routes.post('/n8n/jobs/delete')
async def delete_job_route(request):
    try:
        expected = KEY_FILE.read_text(encoding='ascii').strip()
        if not re.fullmatch('[a-f0-9]{64}', expected):
            return web.json_response({'ok': False, 'error': 'Invalid server key'}, status=503)
        supplied = request.headers.get('Authorization', '')
        if not hmac.compare_digest(supplied, 'Bearer ' + expected):
            return web.json_response({'ok': False, 'error': 'Unauthorized'}, status=401)
        if request.content_length is None or request.content_length > 1024:
            return web.json_response({'ok': False, 'error': 'Invalid body length'}, status=400)
        body = await request.json()
        if not isinstance(body, dict) or set(body) != {'request_id'}:
            raise ValueError('Expected request_id only')
        # Synchronous, small local cleanup: no async gap between idle check and deletion.
        return web.json_response(delete_job(body['request_id']))
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        return web.json_response({'ok': False, 'error': str(exc)}, status=409)


NODE_CLASS_MAPPINGS = {}
NODE_DISPLAY_NAME_MAPPINGS = {}

# Recovery and idempotent submission. A single async gate orders submissions and snapshots.
import asyncio
import hashlib
import time
import uuid
from aiohttp import ClientSession, ClientTimeout

BOOT_ID = uuid.uuid4().hex
BOOT_STARTED = time.time()
PROTOCOL_VERSION = 2
PLUGIN_VERSION = '2026.10.24-aspect-1'
_GATE = asyncio.Lock()
SUBMISSIONS = STATE_ROOT / 'submissions'
SUBMISSIONS.mkdir(parents=True, exist_ok=True)


def _atomic_json(path, data):
    temporary = path.with_name(path.name + '.tmp-' + uuid.uuid4().hex)
    try:
        with temporary.open('x', encoding='utf-8') as stream:
            json.dump(data, stream)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


_atomic_json(STATE_ROOT / 'comfy-boot.json', {'boot_id': BOOT_ID, 'started_at': BOOT_STARTED})


def _authorized(request):
    key = KEY_FILE.read_text(encoding='ascii').strip()
    return bool(re.fullmatch('[a-f0-9]{64}', key)) and hmac.compare_digest(request.headers.get('Authorization', ''), 'Bearer ' + key)


@PromptServer.instance.routes.get('/n8n/jobs/health')
async def health_route(request):
    if not _authorized(request):
        return web.json_response({'ok': False}, status=401)
    finalizer_named_output = False
    try:
        import nodes
        finalizer_available = 'N8NMoveFinalVideo' in nodes.NODE_CLASS_MAPPINGS
        finalizer_class = nodes.NODE_CLASS_MAPPINGS.get('N8NMoveFinalVideo')
        if finalizer_class and hasattr(finalizer_class, 'INPUT_TYPES'):
            finalizer_named_output = 'final_basename' in finalizer_class.INPUT_TYPES().get('optional', {})
    except (ImportError, AttributeError):
        finalizer_available = None
    return web.json_response({
        'ok': True, 'protocol_version': PROTOCOL_VERSION, 'plugin_version': PLUGIN_VERSION,
        'boot_id': BOOT_ID, 'shared_root': str(SHARED_MEDIA_ROOT),
        'output_root': str(folder_paths.get_output_directory()),
        'finalizer_available': finalizer_available, 'finalizer_named_output': finalizer_named_output,
        'capabilities': ['submit', 'recovery-snapshot', 'delete', 'reservation-validation', 'rejection-receipts', 'aspect-ratio-v1'],
    })


def _valid_id(value):
    return isinstance(value, str) and re.fullmatch(r'tg-0-[0-9]+', value)


def _job(request_id):
    if not _valid_id(request_id):
        raise ValueError('Invalid request_id')
    return json.loads((STATE_ROOT / 'scheduler' / 'jobs' / (request_id + '.json')).read_text(encoding='utf-8'))


def _video(info, request_id):
    if not isinstance(info, dict) or info.get('type') != 'output': return None
    name, sub = info.get('filename', ''), info.get('subfolder', '').replace('\\', '/')
    if not re.fullmatch(r'[A-Za-z0-9_.-]+\.mp4', name): return None
    if not re.fullmatch(r'video/n8n/' + re.escape(request_id) + r'(?:-e[0-9]+)?', sub): return None
    root = Path(folder_paths.get_output_directory()).resolve()
    file = root / sub / name
    if file.is_symlink() or not file.resolve().is_relative_to(root) or not file.is_file(): return None
    size = file.stat().st_size
    if size <= 0 or (info.get('checkpoint_bytes') is not None and size != info['checkpoint_bytes']): return None
    return dict(info, filename=name, subfolder=sub, container_path='/comfy-output/' + sub + '/' + name,
                relative_path=sub + '/' + name, windows_path=str(file), checkpoint_bytes=size)


def _probe_complete(file, seconds, fps, final=False, dimensions=None):
    """Read one frame at a time, never a video-sized tensor or a GPU model."""
    try:
        import av  # Already used by ComfyUI video IO; no package is installed here.
        count = 0
        with av.open(str(file)) as container:
            stream = container.streams.video[0]
            rate = float(stream.average_rate or 0)
            if abs(rate - fps) > 0.5 or not (0 < stream.width <= 4096 and 0 < stream.height <= 4096): return False
            if final and (stream.width, stream.height) != (dimensions or (1080, 1920)): return False
            for frame in container.decode(video=0):
                count += 1
                if count > (seconds + 0.5) * fps + 2: return False
        return (seconds - 0.25) * fps <= count <= (seconds + 0.5) * fps + 2
    except Exception:
        return False


def _orphan_video(request_id, seconds, interpolation=False):
    root = Path(folder_paths.get_output_directory()).resolve()
    parent = root / 'video' / 'n8n'
    folders = [parent / request_id] if not interpolation else list(parent.glob(request_id + '-e*'))
    prefix, fps = ('interpolation_', 60) if interpolation else ('ltx_', 30)
    for folder in reversed(sorted(folders)):
        if not folder.is_dir() or folder.is_symlink() or not folder.resolve().is_relative_to(root): continue
        for file in reversed(sorted(folder.glob(prefix + '*.mp4'))):
            if file.is_symlink() or not file.resolve().is_relative_to(root): continue
            if _probe_complete(file, seconds, fps):
                return _video({'filename': file.name, 'subfolder': folder.relative_to(root).as_posix(), 'type': 'output'}, request_id)
    return None


def _expected_final_size(request):
    # Requests created before format selection keep their previous delivery dimensions.
    if 'aspect_ratio' not in request: return None
    if request['aspect_ratio'] == '9:16': return (1088, 1920)
    if request['aspect_ratio'] == '16:9': return (1920, 1088)
    raise ValueError('Invalid saved aspect_ratio')


def _matches_dimensions(file, dimensions):
    # Metadata only: no frames, GPU models or video-sized tensors are loaded.
    try:
        import av
        with av.open(str(file)) as container:
            stream = container.streams.video[0]
            return (stream.width, stream.height) == dimensions
    except Exception:
        return False


def _final_receipt(request_id, seconds, dimensions=None):
    final = SHARED_MEDIA_ROOT / 'final'
    suspicious = False
    if not final.is_dir(): return None, False
    for file in [final / (request_id + '.mp4'), *sorted(final.glob(request_id + '-e*.mp4'))]:
        if not file.exists(): continue
        if not re.fullmatch(re.escape(request_id) + r'(?:-e[0-9]+)?\.mp4', file.name): continue
        if file.is_symlink():
            suspicious = True; continue
        if dimensions is not None and not _matches_dimensions(file, dimensions):
            suspicious = True; continue
        receipt = final / ('.' + file.stem + '.done.json')
        if not receipt.is_file():
            if file.is_symlink() or not _probe_complete(file, seconds, 60, final=True, dimensions=dimensions):
                suspicious = True; continue
            digest = hashlib.sha256()
            with file.open('rb') as stream:
                for block in iter(lambda: stream.read(1024*1024), b''): digest.update(block)
            recovered_run = file.stem
            if file.stem == request_id:
                job_file = STATE_ROOT / 'scheduler' / 'jobs' / (request_id + '.json')
                saved_job = json.loads(job_file.read_text(encoding='utf-8')) if job_file.is_file() else {}
                recovered_run = saved_job.get('postprocess_run_id') or (saved_job.get('checkpoint_interpolated') or {}).get('postprocess_run_id')
                if not isinstance(recovered_run, str) or not re.fullmatch(re.escape(request_id) + r'-e[0-9]+', recovered_run):
                    suspicious = True; continue
            data = {'filename': file.name, 'windows_path': str(file), 'bytes': file.stat().st_size,
                    'moved': True, 'run_id': recovered_run, 'sha256': digest.hexdigest()}
            if file.stem == request_id: data['job_id'] = request_id
            _atomic_json(receipt, data)
            return data, False
        data = json.loads(receipt.read_text(encoding='utf-8'))
        if file.stem == request_id and not (data.get('job_id') == request_id and re.fullmatch(re.escape(request_id) + r'-e[0-9]+', str(data.get('run_id', '')))):
            suspicious = True; continue
        if file.is_symlink() or data.get('filename') != file.name or data.get('bytes') != file.stat().st_size:
            suspicious = True; continue
        digest = hashlib.sha256()
        with file.open('rb') as stream:
            for block in iter(lambda: stream.read(1024*1024), b''): digest.update(block)
        if not hmac.compare_digest(digest.hexdigest(), str(data.get('sha256', ''))): suspicious = True; continue
        return data, False
    return None, suspicious


def recovery_snapshot():
    q = PromptServer.instance.prompt_queue
    running, pending = q.get_current_queue()
    if running or pending: return {'ok': True, 'boot_id': BOOT_ID, 'running': len(running), 'pending': len(pending), 'jobs': []}
    history = q.get_history(max_items=128)
    jobs = []
    for path in sorted((STATE_ROOT / 'scheduler' / 'jobs').glob('tg-0-*.json')):
        j = json.loads(path.read_text(encoding='utf-8'))
        if j.get('status') != 'recovering': continue
        request_id = j['request_id']
        if not _valid_id(request_id): continue
        request = j.get('request')
        seconds = request.get('duration_seconds', 0) if isinstance(request, dict) else 0
        submission_uncertain = _submission_is_uncertain(request_id)
        if seconds not in [2, 4, 6, 8, 10]:
            jobs.append({'request_id': request_id, 'invalid_request': True, 'submission_uncertain': submission_uncertain, 'error': 'duration_seconds must be 2, 4, 6, 8 or 10'})
            if len(jobs) >= 200: break
            continue
        try:
            dimensions = _expected_final_size(request)
        except ValueError:
            jobs.append({'request_id': request_id, 'invalid_request': True, 'submission_uncertain': submission_uncertain, 'error': 'aspect_ratio must be 9:16 or 16:9'})
            if len(jobs) >= 200: break
            continue
        final, suspicious = _final_receipt(request_id, seconds, dimensions)
        video = _video((j.get('checkpoint_review') or {}).get('video') or j.get('video'), request_id)
        interp = _video((j.get('checkpoint_interpolated') or {}).get('interpolated_video') or j.get('interpolated_video'), request_id)
        for entry in history.values():
            if entry.get('status', {}).get('completed') is not True or entry.get('status', {}).get('status_str') != 'success': continue
            for node, stage in [('75', 'ltx'), ('7', 'interpolation')]:
                out = entry.get('outputs', {}).get(node, {})
                for info in [*out.get('images', []), *out.get('videos', []), *out.get('gifs', [])]:
                    if not isinstance(info, dict) or not info.get('filename', '').startswith(stage + '_'): continue
                    known = _video(info, request_id)
                    if known:
                        if stage == 'ltx': video = known
                        else: interp = known
        try:
            import av
            probe_available = True
        except ImportError:
            probe_available = False
        unverified_video = False
        if not video:
            video = _orphan_video(request_id, seconds)
            existing_folder = Path(folder_paths.get_output_directory()) / 'video' / 'n8n' / request_id
            unverified_video = not probe_available and any(existing_folder.glob('ltx_*.mp4'))
        if not interp and j.get('approved'): interp = _orphan_video(request_id, seconds, interpolation=True)
        image = j.get('request', {}).get('image', '')
        image_ok = False
        if re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]*\.(?:png|jpe?g|webp)', image, re.I):
            frame = SHARED_MEDIA_ROOT / 'current' / image
            image_ok = frame.is_file() and not frame.is_symlink() and frame.stat().st_size > 0
            archive = STATE_ROOT / 'jobs' / (request_id + '.json')
            if image_ok and archive.is_file():
                draft = json.loads(archive.read_text(encoding='utf-8')).get('draft', {})
                if draft.get('image_bytes') is not None and frame.stat().st_size != draft['image_bytes']: image_ok = False
                if draft.get('image_mtime') is not None and abs(frame.stat().st_mtime * 1000 - draft['image_mtime']) > 1: image_ok = False
        jobs.append({'request_id': request_id, 'submission_uncertain': submission_uncertain, 'video': video, 'interpolated_video': interp,
                     'final_video': final, 'unverified_final': suspicious, 'unverified_video': unverified_video, 'image_available': image_ok})
        if len(jobs) >= 200: break
    return {'ok': True, 'boot_id': BOOT_ID, 'running': len(running), 'pending': len(pending), 'jobs': jobs}


@PromptServer.instance.routes.post('/n8n/jobs/recovery-snapshot')
async def recovery_snapshot_route(request):
    if not _authorized(request): return web.json_response({'ok': False}, status=401)
    async with _GATE:
        try: return web.json_response(recovery_snapshot())
        except (OSError, ValueError) as exc: return web.json_response({'ok': False, 'error': str(exc)}, status=409)


def _accepted_client(client_id):
    q = PromptServer.instance.prompt_queue
    running, pending = q.get_current_queue()
    for item in [*running, *pending]:
        if len(item) > 3 and item[3].get('client_id') == client_id:
            return {'prompt_id': item[1], 'number': item[0], 'node_errors': {}}
    for prompt_id, entry in q.get_history(max_items=128).items():
        prompt = entry.get('prompt', [])
        if len(prompt) > 3 and prompt[3].get('client_id') == client_id:
            return {'prompt_id': prompt_id, 'number': prompt[0], 'node_errors': {}}
    return None


def _submission_is_uncertain(request_id):
    uncertain = False
    for attempt in SUBMISSIONS.glob(request_id + '-*.json'):
        saved = json.loads(attempt.read_text(encoding='utf-8'))
        if saved.get('boot_id') != BOOT_ID or saved.get('response', {}).get('prompt_id') or saved.get('outcome') == 'rejected':
            continue
        accepted = _accepted_client(saved.get('client_id'))
        if accepted:
            _atomic_json(attempt, dict(saved, response=accepted))
        else:
            uncertain = True
    return uncertain


async def _submit(body, port):
    request_id, owner, stage = body.get('request_id'), body.get('execution_id'), body.get('stage')
    j = _job(request_id)
    if stage not in ['generation', 'interpolation', 'upscale'] or str(j.get('execution_id')) != owner or j.get('cancel_requested') or j.get('status') in ['recovering', 'failed', 'finished', 'rejected', 'cancelled', 'deleted', 'deleting']:
        return {'error': 'obsolete_or_cancelled_worker'}, 409
    graph = body.get('request')
    if not isinstance(graph, dict) or not isinstance(graph.get('prompt'), dict): return {'error': 'invalid_graph'}, 400
    ticket = str(j.get('recovery', {}).get('ticket') or ('original-' + owner))
    if not re.fullmatch(r'[A-Za-z0-9_-]{1,120}', ticket): return {'error': 'invalid_ticket'}, 400
    client = request_id + '-' + stage + '-' + ticket
    graph = dict(graph, client_id=client)
    digest = hashlib.sha256(json.dumps(graph, sort_keys=True).encode()).hexdigest()
    file = SUBMISSIONS / (client + '.json')
    old = json.loads(file.read_text(encoding='utf-8')) if file.exists() else None
    if old and old.get('boot_id') == BOOT_ID:
        if old.get('digest') != digest: return {'error': 'submission_payload_changed'}, 409
        if old.get('response', {}).get('prompt_id'): return old['response'], 200
        if old.get('outcome') == 'rejected':
            return old['response'], old['response_status']
        accepted = _accepted_client(client)
        if accepted:
            _atomic_json(file, dict(old, response=accepted))
            return accepted, 200
        return {'error': 'submission_uncertain', 'message': 'No automatic duplicate submission; use recovery.'}, 409
    control_file = STATE_ROOT / 'scheduler' / 'control.json'
    control = json.loads(control_file.read_text(encoding='utf-8')) if control_file.is_file() else {}
    lease = control.get('lease') or {}
    expected_kind = 'generation-submit' if stage == 'generation' else 'postprocess'
    expected_status = {'generation': 'generation_submitting', 'interpolation': 'interpolating', 'upscale': 'upscaling'}[stage]
    if control.get('paused') or control.get('stop_pending') or lease.get('blocked') or str(lease.get('owner')) != owner or lease.get('request_id') != request_id or lease.get('kind') != expected_kind or j.get('status') != expected_status:
        return {'error': 'submission_reservation_required', 'message': 'The current job does not own the required stage reservation.'}, 409
    _atomic_json(file, {'boot_id': BOOT_ID, 'digest': digest, 'client_id': client, 'intent': True})
    async with ClientSession(timeout=ClientTimeout(total=55)) as session:
        async with session.post('http://127.0.0.1:' + str(port) + '/prompt', json=graph) as response:
            data = await response.json()
            if response.status >= 400:
                # A definitive validation rejection is not an unknown in-flight submission.
                # Treat only explicit 4xx rejection as final; 5xx may be ambiguous.
                if response.status in [400, 401, 403, 404, 405, 413, 415, 422, 429]:
                    _atomic_json(file, {'boot_id': BOOT_ID, 'digest': digest, 'client_id': client,
                                        'intent': False, 'outcome': 'rejected', 'response': data,
                                        'response_status': response.status})
                return data, response.status
    if not isinstance(data, dict) or not data.get('prompt_id'): return {'error': 'submission_unconfirmed'}, 503
    _atomic_json(file, {'boot_id': BOOT_ID, 'digest': digest, 'client_id': client, 'response': data})
    return data, 200


@PromptServer.instance.routes.post('/n8n/jobs/submit')
async def submit_route(request):
    if not _authorized(request): return web.json_response({'error': 'Unauthorized'}, status=401)
    try:
        body = await request.json()
        port = request.transport.get_extra_info('sockname')[1]
        async with _GATE:
            data, status = await _submit(body, port)
        return web.json_response(data, status=status)
    except Exception as exc:
        return web.json_response({'error': 'submission_unconfirmed', 'message': str(exc)}, status=503)

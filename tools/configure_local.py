"""Prepare an isolated local deployment. No service calls, credentials or GPU work."""
import argparse
import ast
import json
from pathlib import Path, PureWindowsPath
import re
import shutil
import tempfile
from urllib.parse import urlsplit

REPO = Path(__file__).resolve().parents[1]


def base_url(value, https=True):
    parsed = urlsplit(value)
    if (parsed.scheme not in (['https'] if https else ['http', 'https'])
            or not parsed.hostname or parsed.username or parsed.password
            or parsed.query or parsed.fragment or parsed.path not in ['', '/']
            or not re.fullmatch(r'[A-Za-z0-9.:-]+', parsed.hostname)
            or any(c in value for c in ["'", '"', '\\', '\n', '\r'])):
        raise ValueError('Use a root URL without credentials, path, query or fragment.')
    try:
        parsed.port
    except ValueError as exc:
        raise ValueError('Invalid URL port.') from exc
    if parsed.hostname.endswith('.invalid'):
        raise ValueError('Replace the .invalid example with your own hostname.')
    return value.rstrip('/')


def prepare(repo, target, user_id, output_root, private_url, public_url,
            comfy_url='http://host.docker.internal:8188', host_port=5681):
    repo, target = Path(repo).resolve(), Path(target).resolve()
    if not re.fullmatch(r'[1-9][0-9]{0,15}', str(user_id)):
        raise ValueError('Telegram user ID must be a positive numeric private-chat ID.')
    if target == repo or target.is_relative_to(repo) or repo.is_relative_to(target):
        raise ValueError('Deployment must be outside, and not an ancestor of, the repository.')
    if target.exists():
        raise ValueError('Deployment directory already exists. Use a new empty target name; nothing overwritten.')
    if not (PureWindowsPath(output_root).is_absolute() or Path(output_root).is_absolute()):
        raise ValueError('Comfy output root must be absolute.')
    if any(c in str(target) + output_root for c in ['\n', '\r', '\x00']):
        raise ValueError('Control characters in paths are not allowed.')
    private_url, public_url = base_url(private_url), base_url(public_url)
    if (urlsplit(public_url).port or 443) not in [443, 80, 88, 8443]:
        raise ValueError('Telegram webhooks require public port 443, 80, 88 or 8443.')
    comfy_url = base_url(comfy_url, https=False)
    if not 1024 <= host_port <= 65535:
        raise ValueError('Choose a host port between 1024 and 65535.')
    media = target / 'media'
    output_root = output_root.replace('\\', '/').rstrip('/')
    if str(media).replace('\\', '/').rstrip('/').lower() == output_root.lower():
        raise ValueError('Media and Comfy output must be different directories.')

    def transform(value, field=''):
        if isinstance(value, dict):
            return {k: transform(v, k) for k, v in value.items()}
        if isinstance(value, list):
            return [transform(v, field) for v in value]
        if not isinstance(value, str):
            return value
        if field == 'chatId' and value == '0':
            return str(user_id)
        if field == 'jsCode':
            value = value.replace('tg-0-', 'tg-' + str(user_id) + '-')
            value = value.replace('/0-0.json', '/' + str(user_id) + '-' + str(user_id) + '.json')
            pattern = r"\b(ALLOWED_CHAT_ID|ALLOWED_USER_ID|telegram_chat_id|chat_id)(\s*(?:=|:)\s*)(['\"])0\3"
            value = re.sub(pattern, lambda m: m[1] + m[2] + m[3] + str(user_id) + m[3], value)
            # Replace an entire JavaScript string literal; never inject raw path text into code.
            value = value.replace("'C:/Users/LOCAL_USER/AppData/Local/Comfy-Desktop/ComfyUI-Shared/output'", json.dumps(output_root))
            # The URL can be used inside a quoted JavaScript string in expressions/Code.
            if "'" in private_url or '"' in private_url or '\\' in private_url:
                raise ValueError('Quotes/backslashes are not allowed in a base URL.')
        return value.replace('https://n8n.example.invalid', private_url).replace(
            'http://host.docker.internal:8188', comfy_url)

    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix='.pipeline-prepare-', dir=target.parent))
    try:
        for relative in ['media/current', 'media/workflows', 'media/final',
                         'deployment/workflows', 'deployment/custom_nodes', 'deployment/tests', 'backups']:
            (temporary / relative).mkdir(parents=True, exist_ok=True)
        for source in sorted((repo / 'workflows').glob('*.template.json')):
            workflow = transform(json.loads(source.read_text(encoding='utf-8-sig')))
            workflow['active'] = False
            workflow['pinData'] = {}
            if workflow.get('credentials') or any(n.get('credentials') for n in workflow['nodes']):
                raise ValueError('Public templates must not bind production credentials.')
            result = json.dumps(workflow, ensure_ascii=False, indent=2) + '\n'
            if 'tg-0-' in result or '/0-0.json' in result or 'LOCAL_USER' in result or 'n8n.example.invalid' in result:
                raise ValueError('Unconfigured marker remains in ' + source.name)
            (temporary / 'deployment/workflows' / source.name.replace('.template', '.local')).write_text(result, encoding='utf-8')
        fixture = repo / 'tests/fixtures/t5-controlled-failure.template.json'
        if fixture.is_file():
            (temporary / 'deployment/tests/t5-controlled-failure.local.json').write_text(
                json.dumps(transform(json.loads(fixture.read_text(encoding='utf-8'))), ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        for name, constant, value in [('n8n_job_control', 'SHARED_MEDIA_ROOT', str(media)),
                                       ('n8n_video_finalizer', 'FINAL_DIRECTORY', str(media / 'final'))]:
            source = repo / 'comfy/custom_nodes' / name / '__init__.py'
            code = source.read_text(encoding='utf-8').replace('tg-0-', 'tg-' + str(user_id) + '-')
            code, changes = re.subn(r'^' + constant + r'\s*=\s*Path\([^\n]+\)$',
                                   lambda _: constant + ' = Path(' + repr(value) + ')', code, flags=re.M)
            if changes != 1:
                raise ValueError('Unexpected custom node constant: ' + constant)
            ast.parse(code)
            destination = temporary / 'deployment/custom_nodes' / name
            destination.mkdir()
            (destination / '__init__.py').write_text(code, encoding='utf-8')
        shutil.copyfile(repo / 'comfy/templates/ltx.json', temporary / 'media/workflows/ltx.json')
        config = {'schema_version': 1, 'telegram_user_id': str(user_id), 'base_root': str(target),
                  'media_root': str(media), 'comfy_output_root': output_root,
                  'private_base_url': private_url, 'public_webhook_base_url': public_url,
                  'comfy_container_url': comfy_url, 'n8n_host_port': host_port}
        (temporary / 'deployment/settings.local.json').write_text(json.dumps(config, indent=2) + '\n', encoding='utf-8')
        compose = {
            'services': {'n8n': {
                'image': 'docker.n8n.io/n8nio/n8n:2.43.7', 'restart': 'unless-stopped',
                'ports': ['127.0.0.1:' + str(host_port) + ':5678'],
                'environment': {
                    'TZ': 'America/Sao_Paulo', 'GENERIC_TIMEZONE': 'America/Sao_Paulo',
                    'N8N_DEFAULT_BINARY_DATA_MODE': 'filesystem',
                    'N8N_RESTRICT_FILE_ACCESS_TO': '/files;/comfy-output',
                    'NODE_FUNCTION_ALLOW_BUILTIN': 'fs', 'N8N_RUNNERS_MODE': 'internal',
                    'N8N_WEBHOOK_URL': public_url + '/', 'N8N_EDITOR_BASE_URL': private_url,
                    'N8N_ENFORCE_SETTINGS_FILE_PERMISSIONS': 'true',
                },
                'volumes': [
                    {'type': 'volume', 'source': 'n8n_data', 'target': '/home/node/.n8n'},
                    {'type': 'bind', 'source': str(media).replace('\\', '/'), 'target': '/files',
                     'bind': {'create_host_path': False}},
                    {'type': 'bind', 'source': output_root, 'target': '/comfy-output', 'read_only': True,
                     'bind': {'create_host_path': False}},
                ],
            }}, 'volumes': {'n8n_data': {}},
        }
        # JSON is a valid YAML document; avoids depending on a YAML package.
        (temporary / 'deployment/compose.local.yaml').write_text(json.dumps(compose, indent=2) + '\n', encoding='utf-8')
        (temporary / 'deployment/BEFORE-START.txt').write_text(
            'Reference lab deployment, not an audited production compose. Configure HTTPS proxy and actual trusted proxy hops; '
            'validate internal runner fs and /proc access before publishing schedules. Import LOCAL workflows, select credentials '
            'and Error Workflow manually. Never reuse a production bot or state/volume for a parallel test. '
            'No services were started and no keys or tokens were generated.\n', encoding='utf-8')
        temporary.rename(target)
    finally:
        if temporary.exists():
            shutil.rmtree(temporary)
    return config


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-root', required=True, type=Path)
    parser.add_argument('--telegram-user-id', required=True)
    parser.add_argument('--comfy-output-root', required=True)
    parser.add_argument('--private-base-url', required=True)
    parser.add_argument('--public-webhook-base-url', required=True)
    parser.add_argument('--comfy-container-url', default='http://host.docker.internal:8188')
    parser.add_argument('--n8n-host-port', type=int, default=5681)
    args = parser.parse_args()
    try:
        result = prepare(REPO, args.base_root, args.telegram_user_id, args.comfy_output_root,
                         args.private_base_url, args.public_webhook_base_url,
                         args.comfy_container_url, args.n8n_host_port)
    except (ValueError, OSError, KeyError, json.JSONDecodeError) as exc:
        parser.exit(1, 'Preparation failed: ' + str(exc) + '\n')
    print('Prepared:', result['base_root'])
    print('5 normal workflows and a separate T5 fixture; no services started, no production files overwritten.')


if __name__ == '__main__':
    main()

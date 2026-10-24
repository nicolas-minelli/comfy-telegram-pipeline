"""Move only the completed MP4 of one n8n VHS job into a fixed final directory.

No network endpoint, shell command or third-party dependency is added.
Install this directory under ComfyUI/custom_nodes and restart ComfyUI.
"""

import json
import hashlib
import os
from pathlib import Path
import re
import shutil
import uuid

import folder_paths


# Edit this ONE constant if your final directory is different.
FINAL_DIRECTORY = Path(r"E:\AI\media\final")
COPY_BUFFER_SIZE = 1024 * 1024


def _digest(path):
    checksum = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(COPY_BUFFER_SIZE), b""):
            checksum.update(block)
    return checksum.digest()


def _same_content(left, right):
    return left.stat().st_size == right.stat().st_size and _digest(left) == _digest(right)


def _publish_without_overwrite(temporary, destination):
    if os.name == "nt":
        # Windows rename refuses an existing destination, including a race.
        os.rename(temporary, destination)
    else:
        # Testable on POSIX too, without rename's overwrite behavior.
        os.link(temporary, destination)
        temporary.unlink()


class N8NMoveFinalVideo:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "filenames": ("VHS_FILENAMES",),
            "run_id": ("STRING", {"default": "", "multiline": False}),
        }, "optional": {"final_basename": ("STRING", {"default": "", "multiline": False})}}

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("final_path",)
    FUNCTION = "move_final_video"
    CATEGORY = "n8n/Video"
    OUTPUT_NODE = True

    def move_final_video(self, filenames, run_id, final_basename=""):
        if not isinstance(run_id, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,160}", run_id):
            raise ValueError("Invalid n8n run_id")
        if final_basename:
            if not isinstance(final_basename, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,80}", final_basename) or not re.fullmatch(re.escape(final_basename) + r"-e[0-9]+", run_id):
                raise ValueError("Final basename must identify this run's job")
        basename = final_basename or run_id
        if not isinstance(filenames, (tuple, list)) or len(filenames) != 2 or filenames[0] is not True:
            raise ValueError("Expected VHS filenames from save_output=true")
        paths = filenames[1]
        if not isinstance(paths, (tuple, list)):
            raise ValueError("Invalid VHS file list")
        if not paths:
            # VHS returns an empty list while Meta Batch still has work to do.
            return {"ui": {"pending": [True]}, "result": ("",)}

        # The last MP4 is the audio mux when VHS generated one.
        candidates = [Path(path) for path in paths if isinstance(path, str) and path.lower().endswith(".mp4")]
        if not candidates:
            raise ValueError("VHS did not produce an MP4")
        candidate = candidates[-1]
        output_root = Path(folder_paths.get_output_directory()).resolve()
        expected_directory = (output_root / "video" / "n8n" / run_id).resolve()
        if not expected_directory.is_relative_to(output_root):
            raise ValueError("Job directory escapes output root")
        source = candidate.resolve()
        if source.parent != expected_directory or not re.fullmatch(r"upscale_[A-Za-z0-9_.-]+\.mp4", source.name):
            raise ValueError("Refusing to move a file outside this job's upscale output")
        final_root = FINAL_DIRECTORY.expanduser().resolve()
        final_root.mkdir(parents=True, exist_ok=True)
        destination = final_root / (basename + ".mp4")
        if source == destination:
            raise ValueError("Final directory must differ from the render destination")
        lock = final_root / ("." + basename + ".move.lock")
        temporary = final_root / ("." + basename + ".partial-" + uuid.uuid4().hex)

        # A process crash can leave a lock; inspect it before removing manually.
        descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        os.close(descriptor)
        try:
            if destination.exists():
                # Recover safely if publication succeeded but source deletion failed.
                if not destination.is_file() or destination.stat().st_size == 0:
                    raise FileExistsError("Destination already exists and is not a valid file")
                if source.exists():
                    if not _same_content(source, destination):
                        raise FileExistsError("Destination already exists with different content; nothing overwritten")
                    source.unlink()
            else:
                if not source.is_file() or source.stat().st_size == 0:
                    raise FileNotFoundError("Completed source MP4 is missing or empty")
                before = source.stat()
                with source.open("rb") as original, temporary.open("xb") as target:
                    shutil.copyfileobj(original, target, length=COPY_BUFFER_SIZE)
                    target.flush()
                    os.fsync(target.fileno())
                after = source.stat()
                if before.st_size != after.st_size or before.st_mtime_ns != after.st_mtime_ns:
                    raise RuntimeError("Source changed during finalization; original kept")
                if not _same_content(source, temporary):
                    raise RuntimeError("Copy verification failed; original kept")
                _publish_without_overwrite(temporary, destination)
                source.unlink()
            info = {"filename": destination.name, "windows_path": str(destination),
                    "bytes": destination.stat().st_size, "moved": True, "run_id": run_id}
            # A durable receipt lets recovery recognize publication even if n8n/ComfyUI
            # crashes before recording the HTTP history or final completion.
            info['sha256'] = _digest(destination).hex()
            if final_basename: info['job_id'] = final_basename
            receipt = final_root / ('.' + basename + '.done.json')
            receipt_temp = final_root / ('.' + run_id + '.receipt-' + uuid.uuid4().hex)
            try:
                with receipt_temp.open('x', encoding='utf-8') as stream:
                    json.dump(info, stream)
                    stream.flush()
                    os.fsync(stream.fileno())
                os.replace(receipt_temp, receipt)
            finally:
                receipt_temp.unlink(missing_ok=True)
            return {"ui": {"final_video": [info]}, "result": (str(destination),)}
        finally:
            temporary.unlink(missing_ok=True)
            lock.unlink(missing_ok=True)


NODE_CLASS_MAPPINGS = {"N8NMoveFinalVideo": N8NMoveFinalVideo}
NODE_DISPLAY_NAME_MAPPINGS = {"N8NMoveFinalVideo": "Move Final Video to Final Folder (n8n)"}
__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]

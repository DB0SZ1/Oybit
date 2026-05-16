import tempfile
import os
import fcntl
from pathlib import Path

def atomic_write(path: Path, content: str):
    """Write to temp file then rename — atomic on POSIX systems."""
    dir_path = path.parent
    dir_path.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode='w',
        dir=dir_path,
        delete=False,
        suffix='.tmp',
        encoding='utf-8'
    ) as tmp:
        tmp.write(content)
        tmp_path = tmp.name
    os.replace(tmp_path, path)  # atomic rename

def append_to_simulation_log(log_path: Path, entry: str):
    """Append to a log file using exclusive locks to prevent concurrency errors."""
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, 'a', encoding='utf-8') as f:
        fcntl.flock(f, fcntl.LOCK_EX)  # exclusive lock
        try:
            f.write(entry + '\n')
            f.flush()
            os.fsync(f.fileno())
        finally:
            fcntl.flock(f, fcntl.LOCK_UN)  # always release

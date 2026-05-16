import subprocess
from pathlib import Path

def run_command(args: list, cwd: Path = None, timeout: int = 300) -> tuple[int, str, str]:
    """
    Safe subprocess wrapper. Never use shell=True.
    Returns (returncode, stdout, stderr)
    """
    result = subprocess.run(
        args,
        capture_output=True,
        text=True,
        cwd=str(cwd) if cwd else None,
        timeout=timeout,
        shell=False,  # NEVER True
        encoding='utf-8',
        errors='replace'
    )
    return result.returncode, result.stdout, result.stderr

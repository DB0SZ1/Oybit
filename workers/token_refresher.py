import os
import sys
os.environ['PYTHONIOENCODING'] = 'utf-8'
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

"""
Oybit — Token Refresher Worker
Checks and refreshes tokens every TOKEN_REFRESH_INTERVAL seconds.
"""
import logging
import time
import signal

from backend.token_store.refresher import run_refresh_cycle
from backend.config import TOKEN_REFRESH_INTERVAL

_running = True

def _handle_sigterm(signum, frame):
    global _running
    _running = False

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s"
    )
    logger = logging.getLogger("token_refresher")
    signal.signal(signal.SIGTERM, _handle_sigterm)
    logger.info(f"Token refresher started — runs every {TOKEN_REFRESH_INTERVAL}s")

    while _running:
        try:
            run_refresh_cycle()
        except Exception as e:
            logger.error(f"Refresh cycle error: {e}")
        time.sleep(TOKEN_REFRESH_INTERVAL)

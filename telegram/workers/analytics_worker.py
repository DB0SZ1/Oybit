import os
import sys
os.environ['PYTHONIOENCODING'] = 'utf-8'
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

"""
Oybit — Analytics Worker
Runs analytics aggregation on schedule.
"""
import logging
import schedule
import time
import signal
import os

from analytics.aggregator import run_aggregation
from config import ANALYTICS_RUN_HOUR

_running = True

def _handle_sigterm(signum, frame):
    global _running
    _running = False

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s"
    )
    logger = logging.getLogger("analytics_worker")
    signal.signal(signal.SIGTERM, _handle_sigterm)

    schedule.every().day.at(f"{ANALYTICS_RUN_HOUR:02d}:00").do(run_aggregation)
    logger.info(f"Analytics worker started — runs daily at {ANALYTICS_RUN_HOUR:02d}:00")

    while _running:
        schedule.run_pending()
        time.sleep(60)

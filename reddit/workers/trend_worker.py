import os
import sys
os.environ['PYTHONIOENCODING'] = 'utf-8'
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

"""
Oybit — Trend Worker
Runs trend collection on schedule.
"""
import logging
import schedule
import time
import signal

from intelligence.trend_aggregator import run_trend_collection
from config import TREND_RUN_HOUR

_running = True

def _handle_sigterm(signum, frame):
    global _running
    _running = False

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s"
    )
    logger = logging.getLogger("trend_worker")
    signal.signal(signal.SIGTERM, _handle_sigterm)

    schedule.every().day.at(f"{TREND_RUN_HOUR:02d}:00").do(run_trend_collection)
    logger.info(f"Trend worker started — runs daily at {TREND_RUN_HOUR:02d}:00")

    while _running:
        schedule.run_pending()
        time.sleep(60)

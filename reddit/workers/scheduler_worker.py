import os
import sys
os.environ['PYTHONIOENCODING'] = 'utf-8'
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

"""
Oybit — Scheduler Worker
Runs the scheduler dispatch loop continuously.
Entry point for Railway worker process.
"""
import logging
from scheduler_worker.cron import run_scheduler

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s"
    )
    run_scheduler()

import os
import sys
os.environ['PYTHONIOENCODING'] = 'utf-8'
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

"""
MiroFish Worker — Agent A
Runs daily to populate the narrative_forecast_72h.
"""

import time
import schedule
import signal
from datetime import datetime
from backend.logger import get_logger
from backend.db.session import SessionLocal
from backend.db.models import WorkerHeartbeat
from backend.intelligence.mirofish.narrative_forecaster import run_daily_forecast

logger = get_logger("mirofish_worker")

shutdown = False

def sigterm_handler(signum, frame):
    global shutdown
    logger.info("SIGTERM received. Preparing to shut down...")
    shutdown = True

def record_heartbeat():
    try:
        db = SessionLocal()
        hb = db.query(WorkerHeartbeat).filter_by(worker_name="mirofish_worker").first()
        if not hb:
            hb = WorkerHeartbeat(worker_name="mirofish_worker", status="running", last_beat=datetime.utcnow())
            db.add(hb)
        else:
            hb.status = "running"
            hb.last_beat = datetime.utcnow()
        db.commit()
        db.close()
    except Exception as e:
        logger.error(f"Failed to record heartbeat: {e}")

# Normally reads from env, but mock for this implementation
MIROFISH_RUN_HOUR = "05:00"

def job():
    print("MiroFish Worker: Running daily forecast...")
    try:
        results = run_daily_forecast()
        # In actual execution, we'd save results to MiroFishRun table
        print(f"MiroFish Worker: Successfully ran forecast. Extracted {len(results.get('rising_narratives', []))} narratives.")
    except Exception as e:
        print(f"MiroFish Worker: Run failed: {e}")

def start_worker():
    signal.signal(signal.SIGTERM, sigterm_handler)
    schedule.every().day.at(MIROFISH_RUN_HOUR).do(job)
    logger.info(f"MiroFish Worker started. Scheduled for {MIROFISH_RUN_HOUR} daily.")
    
    while not shutdown:
        schedule.run_pending()
        record_heartbeat()
        time.sleep(60)
        
    logger.info("MiroFish Worker shut down gracefully.")

if __name__ == "__main__":
    start_worker()

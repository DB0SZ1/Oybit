"""
Oybit — MiroFish Worker
Runs daily to collect intelligence and forecast narratives.
"""
import time
import logging
from datetime import datetime
import schedule

from backend.db.session import get_db, SessionLocal
from backend.db.models import WorkerHeartbeat
from backend.intelligence.mirofish.narrative_forecaster import run_daily_forecast

logger = logging.getLogger("mirofish_worker")


def update_heartbeat(status: str, error: str = None):
    db = SessionLocal()
    try:
        hb = db.query(WorkerHeartbeat).filter_by(worker_name="mirofish_worker").first()
        if not hb:
            hb = WorkerHeartbeat(worker_name="mirofish_worker")
            db.add(hb)
        
        hb.last_heartbeat = datetime.utcnow()
        hb.status = "running" if status == "ok" else "error"
        if status == "ok" and not error:
            hb.last_run = datetime.utcnow()
            hb.last_status = "ok"
        if error:
            hb.last_error = error
        
        db.commit()
    except Exception as e:
        logger.error(f"Failed to update heartbeat: {e}")
    finally:
        db.close()


def run_mirofish_job():
    logger.info("Starting MiroFish intelligence job...")
    try:
        run_daily_forecast()
        update_heartbeat("ok")
        logger.info("MiroFish job completed.")
    except Exception as e:
        logger.error(f"MiroFish job failed: {e}")
        update_heartbeat("error", str(e))


def start_worker():
    logging.basicConfig(level=logging.INFO)
    logger.info("MiroFish Worker started")
    update_heartbeat("ok")
    
    # Run once immediately
    run_mirofish_job()
    
    # Schedule to run daily at 5 AM WAT (which is 4 AM UTC)
    schedule.every().day.at("04:00").do(run_mirofish_job)
    
    while True:
        schedule.run_pending()
        time.sleep(60)


if __name__ == "__main__":
    start_worker()

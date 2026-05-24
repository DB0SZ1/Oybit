"""
Oybit — Trend Worker
Runs hourly to collect trend signals from RSS and search.
"""
import time
import logging
from datetime import datetime
import schedule

from backend.db.session import get_db, SessionLocal
from backend.db.models import WorkerHeartbeat
from backend.intelligence.trend_aggregator import run_trend_collection

logger = logging.getLogger("trend_worker")


def update_heartbeat(status: str, error: str = None):
    db = SessionLocal()
    try:
        hb = db.query(WorkerHeartbeat).filter_by(worker_name="trend_worker").first()
        if not hb:
            hb = WorkerHeartbeat(worker_name="trend_worker")
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


def run_trend_job():
    logger.info("Starting trend collection job...")
    try:
        run_trend_collection()
        update_heartbeat("ok")
        logger.info("Trend job completed.")
    except Exception as e:
        logger.error(f"Trend job failed: {e}")
        update_heartbeat("error", str(e))


def start_worker():
    logging.basicConfig(level=logging.INFO)
    logger.info("Trend Worker started")
    update_heartbeat("ok")
    
    # Run once immediately
    run_trend_job()
    # Create isolated scheduler
    scheduler = schedule.Scheduler()
    
    # Schedule to run every hour
    scheduler.every(1).hours.do(run_trend_job)
    
    while True:
        scheduler.run_pending()
        time.sleep(60)


if __name__ == "__main__":
    start_worker()

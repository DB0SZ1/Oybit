"""
Oybit — Analytics Worker
Runs daily to fetch analytics for published posts.
Updates PostAnalytics and AccountDailyMetrics.
"""
import time
import logging
from datetime import datetime
import schedule

from backend.db.session import get_db, SessionLocal
from backend.db.models import WorkerHeartbeat
from backend.analytics.aggregator import run_aggregation

logger = logging.getLogger("analytics_worker")


def update_heartbeat(status: str, error: str = None):
    db = SessionLocal()
    try:
        hb = db.query(WorkerHeartbeat).filter_by(worker_name="analytics_worker").first()
        if not hb:
            hb = WorkerHeartbeat(worker_name="analytics_worker")
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


def run_analytics_job():
    logger.info("Starting analytics collection job...")
    try:
        run_aggregation()
        update_heartbeat("ok")
        logger.info("Analytics collection job completed.")
    except Exception as e:
        logger.error(f"Analytics job failed: {e}")
        update_heartbeat("error", str(e))


def start_worker():
    logging.basicConfig(level=logging.INFO)
    logger.info("Analytics Worker started")
    update_heartbeat("ok")
    
    # Run once immediately
    run_analytics_job()
    
    # Schedule to run every 6 hours
    schedule.every(6).hours.do(run_analytics_job)
    
    while True:
        schedule.run_pending()
        time.sleep(60)


if __name__ == "__main__":
    start_worker()

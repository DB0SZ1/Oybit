"""
Oybit — Feedback Worker
Runs weekly to process post feedback and update the persona.
"""
import time
import logging
from datetime import datetime
import schedule

from backend.db.session import get_db, SessionLocal
from backend.db.models import WorkerHeartbeat
from backend.feedback_loop.learning_engine import run_weekly_learning_cycle

logger = logging.getLogger("feedback_worker")


def update_heartbeat(status: str, error: str = None):
    db = SessionLocal()
    try:
        hb = db.query(WorkerHeartbeat).filter_by(worker_name="feedback_worker").first()
        if not hb:
            hb = WorkerHeartbeat(worker_name="feedback_worker")
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


def run_feedback_job():
    logger.info("Starting feedback learning cycle...")
    try:
        db = SessionLocal()
        try:
            run_weekly_learning_cycle(db)
        finally:
            db.close()
        update_heartbeat("ok")
        logger.info("Feedback learning cycle completed.")
    except Exception as e:
        logger.error(f"Feedback job failed: {e}")
        update_heartbeat("error", str(e))


def start_worker():
    logging.basicConfig(level=logging.INFO)
    logger.info("Feedback Worker started")
    update_heartbeat("ok")
    
    # Run once immediately
    run_feedback_job()
    # Create isolated scheduler
    scheduler = schedule.Scheduler()
    
    # Schedule to run weekly on Sunday at 2 AM
    scheduler.every().sunday.at("02:00").do(run_feedback_job)
    
    while True:
        scheduler.run_pending()
        time.sleep(60)


if __name__ == "__main__":
    start_worker()

"""
Oybit — Scheduler Cron
Main loop: runs dispatcher every SCHEDULER_INTERVAL seconds.
Handles graceful shutdown on SIGTERM.
"""
import signal
import time
import logging

import schedule

from scheduler_worker.dispatcher import run_dispatch_cycle
from config import SCHEDULER_INTERVAL
from db.session import SessionLocal
from db.models import WorkerHeartbeat
from datetime import datetime

logger = logging.getLogger(__name__)

_running = True


def _handle_sigterm(signum, frame):
    global _running
    logger.info("Received SIGTERM — shutting down scheduler gracefully")
    _running = False


def update_heartbeat(status: str, error: str = None):
    db = SessionLocal()
    try:
        hb = db.query(WorkerHeartbeat).filter_by(worker_name="scheduler_worker").first()
        if not hb:
            hb = WorkerHeartbeat(worker_name="scheduler_worker")
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


def safe_run_dispatch_cycle():
    try:
        run_dispatch_cycle()
        update_heartbeat("ok")
    except Exception as e:
        logger.error(f"Scheduler dispatch failed: {e}")
        update_heartbeat("error", str(e))


def run_scheduler():
    """
    Main scheduler loop.
    Runs dispatcher every SCHEDULER_INTERVAL seconds.
    Exits cleanly on SIGTERM.
    """
    global _running
    try:
        signal.signal(signal.SIGTERM, _handle_sigterm)
    except ValueError:
        pass # Running in a background thread where signals aren't allowed

    interval_seconds = SCHEDULER_INTERVAL
    logger.info(f"Scheduler started — dispatching every {interval_seconds}s")
    
    update_heartbeat("ok")

    schedule.every(interval_seconds).seconds.do(safe_run_dispatch_cycle)
    
    # Run the autonomous opportunity polling every 6 hours
    # from scheduler_worker.autonomous_loop import run_opportunity_polling, run_post_verification
    # schedule.every(6).hours.do(run_opportunity_polling)
    
    # Run post verification daily
    # schedule.every().day.at("02:00").do(run_post_verification)

    # Trigger a check immediately on startup to process any unposted logs missed during downtime
    from workers.bip_scheduler import run_bip_batch_cycle
    import threading
    threading.Thread(target=run_bip_batch_cycle, daemon=True).start()

    while _running:
        schedule.run_pending()
        time.sleep(1)

    logger.info("Scheduler stopped")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_scheduler()

import os
import sys
os.environ['PYTHONIOENCODING'] = 'utf-8'
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

"""
Feedback Worker — Agent A
Runs weekly to patch persona.md.
"""

import time
import schedule
import signal
from datetime import datetime
from backend.logger import get_logger
from backend.db.session import SessionLocal
from backend.db.models import WorkerHeartbeat
from backend.feedback_loop.learning_engine import analyze_patterns
from backend.feedback_loop.persona_patcher import apply_persona_patches
from backend.feedback_loop.mirofish_refiner import build_refinement_signal
from backend.feedback_loop.archiver import archive_old_logs

logger = get_logger("feedback_worker")

shutdown = False

def sigterm_handler(signum, frame):
    global shutdown
    logger.info("SIGTERM received. Preparing to shut down...")
    shutdown = True

def record_heartbeat():
    try:
        db = SessionLocal()
        hb = db.query(WorkerHeartbeat).filter_by(worker_name="feedback_worker").first()
        if not hb:
            hb = WorkerHeartbeat(worker_name="feedback_worker", status="running", last_beat=datetime.utcnow())
            db.add(hb)
        else:
            hb.status = "running"
            hb.last_beat = datetime.utcnow()
        db.commit()
        db.close()
    except Exception as e:
        logger.error(f"Failed to record heartbeat: {e}")

FEEDBACK_RUN_DAY = "sunday"
FEEDBACK_RUN_HOUR = "02:00"

def job():
    print("Feedback Worker: Running weekly learning loop...")
    try:
        # 1. Fetch recent posts & patterns from DB (mocked here)
        recent_posts = [] 
        patterns = analyze_patterns(recent_posts)
        
        # 2. Patch persona
        patch_result = apply_persona_patches(
            persona_path="/data/personas/ahmad/persona.md",  # usually from config
            recent_patterns=patterns,
            total_posts=len(recent_posts)
        )
        print(f"Patch applied: {patch_result['success']}, {patch_result['changes']}")
        
        # 3. Inform MiroFish spawner
        refinement_signal = build_refinement_signal(patterns)
        logger.info("Refinement signal built for next MiroFish run.")
        
        # 4. Run data retention archiver
        try:
            db = SessionLocal()
            archive_old_logs(db)
            db.close()
        except Exception as e:
            logger.error(f"Archiver failed: {e}")

    except Exception as e:
        logger.error(f"Feedback Worker: Run failed: {e}")


def start_worker():
    signal.signal(signal.SIGTERM, sigterm_handler)
    schedule.every().sunday.at(FEEDBACK_RUN_HOUR).do(job)
    logger.info(f"Feedback Worker started. Scheduled for {FEEDBACK_RUN_DAY} at {FEEDBACK_RUN_HOUR}.")
    
    while not shutdown:
        schedule.run_pending()
        record_heartbeat()
        time.sleep(60)
        
    logger.info("Feedback Worker shut down gracefully.")

if __name__ == "__main__":
    start_worker()

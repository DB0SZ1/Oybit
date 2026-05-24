"""
Oybit — Opportunity Worker
Runs periodically to detect content opportunities based on intelligence feeds
and auto-triggers the pipeline.
"""
import time
import logging
from datetime import datetime
import schedule

from backend.db.session import get_db, SessionLocal
from backend.db.models import WorkerHeartbeat
from backend.intelligence.opportunity_detector import detect_opportunities

logger = logging.getLogger("opportunity_worker")


def update_heartbeat(status: str, error: str = None):
    db = SessionLocal()
    try:
        hb = db.query(WorkerHeartbeat).filter_by(worker_name="opportunity_worker").first()
        if not hb:
            hb = WorkerHeartbeat(worker_name="opportunity_worker")
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


import random

def _select_format(account: str) -> str:
    """Weighted format selection based on platform best practices."""
    if account == "instagram_brand":
        return random.choices(["carousel", "reel"], weights=[0.6, 0.4])[0]
    elif account == "instagram_personal":
        return random.choices(["reel", "carousel", "text"], weights=[0.5, 0.3, 0.2])[0]
    elif account == "linkedin":
        return random.choices(["text", "carousel"], weights=[0.7, 0.3])[0]
    elif account == "facebook":
        return random.choices(["text", "carousel", "text"], weights=[0.6, 0.2, 0.2])[0]
    return "text"

MAX_POSTS_PER_DAY_PER_ACCOUNT = 5


def _get_today_post_count(db, account: str) -> int:
    """Count how many posts have already been created today for this account."""
    from backend.db.models import Post
    from datetime import date
    today_start = datetime.combine(date.today(), datetime.min.time())
    count = db.query(Post).filter(
        Post.account == account,
        Post.created_at >= today_start
    ).count()
    return count


def run_opportunity_job():
    logger.info("Starting opportunity detection job...")
    try:
        from backend.api.pipeline import run_full_pipeline
        # Fetch latest narratives from MiroFish runs in the database
        db = SessionLocal()
        try:
            from backend.db.models import MiroFishRun
            latest_run = db.query(MiroFishRun).order_by(
                MiroFishRun.created_at.desc()
            ).first()

            if latest_run and latest_run.narratives:
                narratives = latest_run.narratives
                if isinstance(narratives, list):
                    results = detect_opportunities(narratives)
                    logger.info(f"Detected {len(results)} opportunities from {len(narratives)} narratives")
                    
                    # Process opportunities, respecting the daily cap per account
                    for brief in results:
                        for account in brief.target_accounts:
                            # Check daily limit before generating
                            today_count = _get_today_post_count(db, account)
                            if today_count >= MAX_POSTS_PER_DAY_PER_ACCOUNT:
                                logger.info(f"Skipping {account} — already hit daily cap ({today_count}/{MAX_POSTS_PER_DAY_PER_ACCOUNT})")
                                continue
                            
                            fmt = _select_format(account)
                            logger.info(f"Triggering pipeline for {account} ({fmt}): {brief.topic} [{today_count + 1}/{MAX_POSTS_PER_DAY_PER_ACCOUNT}]")
                            try:
                                run_full_pipeline(
                                    db=db,
                                    topic_brief=f"{brief.topic}. {brief.angle}",
                                    platform=account.split("_")[0],
                                    account=account,
                                    format_type=fmt,
                                    dry_run=False
                                )
                            except Exception as e:
                                logger.error(f"Pipeline failed for {account}: {e}")
                else:
                    logger.info("No valid narrative list found, skipping")
            else:
                logger.info("No MiroFish narratives available yet, skipping opportunity detection")
        finally:
            db.close()

        update_heartbeat("ok")
        logger.info("Opportunity detection completed.")
    except Exception as e:
        logger.error(f"Opportunity detection failed: {e}")
        update_heartbeat("error", str(e))


def start_worker():
    logging.basicConfig(level=logging.INFO)
    logger.info("Opportunity Worker started")
    update_heartbeat("ok")
    
    # Wait for MiroFish worker to populate narratives before first detection
    logger.info("Waiting for MiroFish to populate narratives before first run (up to 300s)...")
    wait_time = 0
    while wait_time < 300:
        db = SessionLocal()
        try:
            from backend.db.models import MiroFishRun
            latest_run = db.query(MiroFishRun).first()
            if latest_run:
                logger.info("Found MiroFishRun in DB, starting opportunity detection.")
                break
        finally:
            db.close()
        time.sleep(10)
        wait_time += 10
    
    # Run once after delay
    run_opportunity_job()
    # Create isolated scheduler
    scheduler = schedule.Scheduler()
    
    # Schedule to run every 4 hours
    scheduler.every(4).hours.do(run_opportunity_job)
    
    while True:
        scheduler.run_pending()
        time.sleep(60)


if __name__ == "__main__":
    start_worker()

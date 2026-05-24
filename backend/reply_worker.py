"""
Oybit — Reply Worker
Runs every 15 minutes to poll comments and generate draft replies.
"""
import time
import logging
from datetime import datetime
import schedule

from backend.db.session import get_db, SessionLocal
from backend.db.models import WorkerHeartbeat

logger = logging.getLogger("reply_worker")


def update_heartbeat(status: str, error: str = None):
    db = SessionLocal()
    try:
        hb = db.query(WorkerHeartbeat).filter_by(worker_name="reply_worker").first()
        if not hb:
            hb = WorkerHeartbeat(worker_name="reply_worker")
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


def run_reply_job():
    logger.info("Starting reply polling job...")
    try:
        from backend.db.models import Post
        from backend.reply_manager.monitor import (
            poll_instagram_comments, poll_facebook_comments,
            poll_linkedin_comments, process_comments
        )

        db = SessionLocal()
        try:
            # Get published posts that have platform IDs
            posts = db.query(Post).filter(
                Post.status == "published",
                Post.platform_post_id != None
            ).order_by(Post.published_at.desc()).limit(20).all()

            total_new = 0
            for post in posts:
                try:
                    comments = []
                    if post.account in ("instagram_personal", "instagram_brand"):
                        comments = poll_instagram_comments(post.platform_post_id, post.account)
                    elif post.account == "facebook":
                        comments = poll_facebook_comments(post.platform_post_id)
                    elif post.account == "linkedin":
                        comments = poll_linkedin_comments(post.platform_post_id)

                    if comments:
                        new_replies = process_comments(post.id, post.account, comments)
                        total_new += len(new_replies)
                except Exception as e:
                    logger.warning(f"Failed to poll comments for post {post.id}: {e}")
                    continue

            logger.info(f"Polled {len(posts)} posts, found {total_new} new comments")
        finally:
            db.close()

        update_heartbeat("ok")
        logger.info("Reply polling job completed.")
    except Exception as e:
        logger.error(f"Reply polling job failed: {e}")
        update_heartbeat("error", str(e))


def start_worker():
    logging.basicConfig(level=logging.INFO)
    logger.info("Reply Worker started")
    update_heartbeat("ok")
    
    # Run once immediately
    run_reply_job()
    # Create isolated scheduler
    scheduler = schedule.Scheduler()
    
    # Schedule to run every 15 minutes
    scheduler.every(15).minutes.do(run_reply_job)
    
    while True:
        scheduler.run_pending()
        time.sleep(60)


if __name__ == "__main__":
    start_worker()

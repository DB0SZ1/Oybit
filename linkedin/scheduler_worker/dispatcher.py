"""
Oybit — Scheduler Dispatcher
Reads due jobs → dispatches via publishers → handles retries.
"""
import logging
from datetime import datetime, timedelta

from scheduler_worker.queue import SchedulerQueue
from publishers.dispatcher import dispatch as publisher_dispatch
from publishers.telegram_notifier import send_telegram_notification
from db.models import Notification, Post, get_session

logger = logging.getLogger(__name__)

BACKOFF_MINUTES = [5, 15, 45]

# Per-account automation level (full_auto dispatches, manual skips)
AUTOMATION_LEVELS = {}


def set_automation_level(account: str, level: str):
    """Set automation level for an account (full_auto | semi_auto | manual)."""
    AUTOMATION_LEVELS[account] = level


def get_automation_level(account: str) -> str:
    return AUTOMATION_LEVELS.get(account, "full_auto")


def run_dispatch_cycle(queue: SchedulerQueue = None, dry_run: bool = False,
                       post_data_fetcher=None, engine=None):
    """
    Run a single dispatch cycle:
    1. Get all due jobs
    2. For each job: mark_running → call publisher → mark_done or mark_failed
    3. Handle retries with backoff

    Args:
        queue: SchedulerQueue instance (creates one if None)
        dry_run: pass through to publishers
        post_data_fetcher: callable(post_id) → dict with format, content_text, media_urls
        engine: DB engine for notifications
    """
    if queue is None:
        queue = SchedulerQueue()

    due_jobs = queue.get_due_jobs_for_telegram()
    if not due_jobs:
        logger.debug("No due jobs found for Telegram notification")
        return []

    logger.info(f"Found {len(due_jobs)} due jobs for Telegram")
    results = []

    for job in due_jobs:
        job_id = job["id"]
        post_id = job["post_id"]
        account = job["account"]
        attempts = job["attempts"]

        # Check automation level
        auto_level = get_automation_level(account)
        if auto_level == "manual":
            logger.info(f"Skipping job {job_id} — {account} is set to manual")
            results.append({"job_id": job_id, "status": "skipped", "reason": "manual mode"})
            continue

        # Mark as running
        queue.mark_running(job_id)
        queue.increment_attempts(job_id)

        try:
            # Get post data
            if post_data_fetcher:
                post_data = post_data_fetcher(post_id)
            else:
                from db.session import SessionLocal
                from db.models import Post
                db_session = SessionLocal()
                try:
                    post = db_session.query(Post).filter(Post.id == post_id).first()
                    if post:
                        post_data = {
                            "format": post.format,
                            "content_text": post.content_text,
                            "media_urls": []
                        }
                    else:
                        post_data = {"format": "text", "content_text": f"Post {post_id}", "media_urls": []}
                finally:
                    db_session.close()

            # Dispatch based on account
            if account == "linkedin":
                result = publisher_dispatch(post_data, account=account, dry_run=dry_run)
            else:
                # Fallback platforms (twitter, reddit) go to Telegram
                result = send_telegram_notification(str(post_id), account, post_data.get("content_text", ""), dry_run=dry_run)
                
            account_result = result.get(account, {})

            if account_result.get("success") or account_result.get("dry_run"):
                # Mark as notified so we don't spam
                db = queue._get_db()
                try:
                    db.execute(
                        __import__('sqlalchemy').text("UPDATE posts SET twilio_notified = TRUE WHERE id = :id"),
                        {"id": post_id}
                    )
                    db.commit()
                finally:
                    queue._close_db(db)

                queue.mark_done(job_id)
                logger.info(f"Job {job_id} completed: Telegram notification sent for post {post_id} → {account}")
                results.append({"job_id": job_id, "status": "done", "result": account_result})
            else:
                error = account_result.get("error", "Unknown error")
                raise Exception(error)

        except Exception as e:
            error_msg = str(e)
            new_attempts = attempts + 1
            logger.error(f"Job {job_id} failed (attempt {new_attempts}): {error_msg}")

            if new_attempts >= 3:
                # Final failure
                queue.mark_failed(job_id, error_msg)
                # Update status to failed_final
                # We use internal db access here since queue._connect() is gone
                db = queue._get_db()
                try:
                    # just run an update query via session
                    db.execute(
                        __import__('sqlalchemy').text("UPDATE scheduler_jobs SET status = 'failed_final' WHERE id = :id"),
                        {"id": job_id}
                    )
                    db.commit()
                finally:
                    queue._close_db(db)

                # Create notification
                _create_notification(
                    f"Post {post_id} to {account} failed permanently after 3 attempts: {error_msg}",
                    engine
                )
                results.append({"job_id": job_id, "status": "failed_final", "error": error_msg})
            else:
                # Reschedule with backoff
                backoff = BACKOFF_MINUTES[min(new_attempts - 1, len(BACKOFF_MINUTES) - 1)]
                new_time = datetime.utcnow() + timedelta(minutes=backoff)
                queue.mark_failed(job_id, error_msg)
                queue.reschedule(job_id, new_time)
                logger.info(f"Job {job_id} rescheduled to {new_time} (attempt {new_attempts})")
                results.append({"job_id": job_id, "status": "rescheduled", "next_attempt": new_time.isoformat()})

    return results


def _create_notification(message: str, engine=None):
    """Create a dashboard notification for failed posts."""
    try:
        session = get_session(engine)
        notif = Notification(type="post_failed", message=message, read=False)
        session.add(notif)
        session.commit()
        session.close()
    except Exception as e:
        logger.error(f"Failed to create notification: {e}")

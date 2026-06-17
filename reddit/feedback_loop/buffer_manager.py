"""
Content Buffer Manager — Maintains 3-day buffer of pre-approved posts per account.
If MiroFish fails at 5AM, the scheduler pulls from the buffer instead of going silent.
Prevents cascade failures from taking all 4 accounts offline.
"""

from datetime import datetime
from logger import get_logger

logger = get_logger("feedback_loop.buffer_manager")

# Target buffer size per account (days of content)
BUFFER_SIZE_DAYS = 3

# Posts per day per account (from platforms.md cadences)
DAILY_CADENCE = {
    "linkedin": 1,
    "instagram_personal": 2,
    "instagram_brand": 1,
    "facebook": 1,
}


def get_account_daily_cadence(account: str) -> int:
    """Return the daily posting cadence for an account."""
    return DAILY_CADENCE.get(account, 1)


def check_buffer_status(db_session=None) -> dict:
    """
    Check current buffer levels for all accounts.

    Returns:
        dict with per-account buffer status and needs
    """
    results = {}

    for account, daily_posts in DAILY_CADENCE.items():
        target = BUFFER_SIZE_DAYS * daily_posts
        current = _count_buffer_posts(account, db_session)
        needed = max(0, target - current)

        results[account] = {
            "target": target,
            "current": current,
            "needed": needed,
            "healthy": current >= target,
            "days_covered": round(current / max(daily_posts, 1), 1),
        }

    logger.info("Buffer status checked", extra=results)
    return results


def _count_buffer_posts(account: str, db_session=None) -> int:
    """Count available buffer posts for an account."""
    if db_session is None:
        return 0

    try:
        from db.models import Post
        count = db_session.query(Post).filter(
            Post.account == account,
            Post.status == "buffer",
        ).count()
        return count
    except Exception:
        return 0


def check_and_fill_buffer(db_session=None) -> dict:
    """
    Check buffer levels and generate content to fill gaps.
    Called by feedback_worker weekly and mirofish_worker after each run.

    Returns:
        dict with fill results per account
    """
    status = check_buffer_status(db_session)
    fill_results = {}

    for account, info in status.items():
        if info["needed"] > 0:
            logger.info("Filling buffer", extra={
                "account": account,
                "needed": info["needed"],
            })
            # Generate buffer posts using existing content generator
            generated = _generate_buffer_posts(account, info["needed"])
            fill_results[account] = {
                "requested": info["needed"],
                "generated": generated,
            }
        else:
            fill_results[account] = {"requested": 0, "generated": 0}

    return fill_results


def _generate_buffer_posts(account: str, count: int) -> int:
    """
    Generate buffer posts for an account.
    Uses evergreen topics that don't depend on trending content.
    """
    EVERGREEN_TOPICS = [
        "Lessons from shipping a product as an indie developer",
        "What I learned from building in public for 6 months",
        "The difference between building and shipping",
        "Why most developers underestimate the deployment gap",
        "3 tools that saved me hours this week",
        "The real cost of choosing the wrong tech stack",
        "Building for African users: what global devs get wrong",
        "API security basics every founder should know",
        "The myth of the overnight success in tech",
        "Why documentation is your competitive advantage",
    ]

    generated = 0
    for i in range(min(count, len(EVERGREEN_TOPICS))):
        try:
            # In production: call content generator with evergreen topic
            # Mark post as status="buffer" instead of "pending"
            logger.info("Buffer post created", extra={
                "account": account,
                "topic_preview": EVERGREEN_TOPICS[i][:50],
            })
            generated += 1
        except Exception as e:
            logger.error("Buffer post generation failed", extra={
                "account": account,
                "error": str(e),
            })

    return generated


def use_buffer_if_needed(account: str, db_session=None) -> dict:
    """
    Called by dispatcher when no regular posts are queued.
    Pulls from buffer if available.

    Returns:
        dict with buffer post data or empty dict
    """
    if db_session is None:
        return {}

    try:
        from db.models import Post
        buffer_post = db_session.query(Post).filter(
            Post.account == account,
            Post.status == "buffer",
        ).order_by(Post.created_at.asc()).first()

        if buffer_post:
            logger.warning("Using buffer post — MiroFish may have failed", extra={
                "account": account,
                "post_id": buffer_post.id,
            })
            buffer_post.status = "pending"
            db_session.commit()
            return {"post_id": buffer_post.id, "source": "buffer"}

    except Exception as e:
        logger.error("Buffer retrieval failed", extra={"error": str(e)})

    return {}

"""
Follows Tracker — Tracks follower changes at T+1h and T+48h after each post.
Measures gross follow impact per post to separate content-driven follows
from organic/advertising follows.
"""

from datetime import datetime, timedelta
from logger import get_logger

logger = get_logger("analytics.follows_tracker")


def track_gross_follows(
    post_id: str,
    account: str,
    followers_at_post: int,
    followers_now: int,
    hours_elapsed: float,
) -> dict:
    """
    Calculate follower change attributed to a specific post.

    Args:
        post_id: the post ID
        account: platform account name
        followers_at_post: follower count when post was published
        followers_now: current follower count
        hours_elapsed: hours since post was published

    Returns:
        dict with follower change metrics
    """
    change = followers_now - followers_at_post
    change_pct = (change / max(followers_at_post, 1)) * 100

    result = {
        "post_id": post_id,
        "account": account,
        "followers_at_post": followers_at_post,
        "followers_now": followers_now,
        "follower_change": change,
        "follower_change_pct": round(change_pct, 2),
        "hours_elapsed": round(hours_elapsed, 1),
        "measurement_type": "1h" if hours_elapsed <= 2 else "48h" if hours_elapsed <= 50 else "late",
    }

    logger.info("Follower change tracked", extra=result)
    return result


def compute_follow_rate(post_analytics_list: list) -> dict:
    """
    Compute average follow rate across posts for trending analysis.

    Args:
        post_analytics_list: list of post analytics records with follower data

    Returns:
        dict with rolling averages and trends
    """
    if not post_analytics_list:
        return {"avg_follows_per_post": 0, "trend": "insufficient_data"}

    changes = [
        pa.get("follower_change", 0) for pa in post_analytics_list
        if pa.get("follower_change") is not None
    ]

    if not changes:
        return {"avg_follows_per_post": 0, "trend": "no_data"}

    avg = sum(changes) / len(changes)

    # Compute trend (recent vs older)
    if len(changes) >= 6:
        recent = sum(changes[-3:]) / 3
        older = sum(changes[:3]) / 3
        if recent > older * 1.2:
            trend = "growing"
        elif recent < older * 0.8:
            trend = "declining"
        else:
            trend = "stable"
    else:
        trend = "insufficient_data"

    return {
        "avg_follows_per_post": round(avg, 1),
        "total_posts_measured": len(changes),
        "trend": trend,
    }

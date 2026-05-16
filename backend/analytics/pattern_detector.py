"""
Oybit — Pattern Detector (lightweight)
Finds top posts by engagement in recent history.
Deep analysis is Agent A's job — this just surfaces basic patterns.
"""
import logging
from backend.db.models import Post, PostAnalytics, get_session

logger = logging.getLogger(__name__)


def detect_patterns(days: int = 30, engine=None) -> dict:
    """
    Basic pattern detection: find top 5 posts by engagement_score in last N days.

    Returns summary dict for Agent A's learning engine.
    """
    from datetime import datetime, timedelta

    session = get_session(engine)
    try:
        cutoff = datetime.utcnow() - timedelta(days=days)
        top_posts = session.query(Post).filter(
            Post.engagement_score != None,
            Post.published_at != None,
            Post.published_at >= cutoff
        ).order_by(Post.engagement_score.desc()).limit(5).all()

        patterns = {
            "top_posts": [],
            "detected_at": datetime.utcnow().isoformat(),
            "period_days": days
        }

        for post in top_posts:
            patterns["top_posts"].append({
                "post_id": post.id,
                "account": post.account,
                "hook_type": post.hook_type,
                "topic_pillar": post.topic_pillar,
                "format": post.format,
                "engagement_score": post.engagement_score
            })

        return patterns
    finally:
        session.close()

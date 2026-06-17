"""
Learning Engine — Agent A Module

Takes MiroFish pre-publish gate result + Real engagement score.
Engagement score: saves*5 + shares*3 + comments*2 + follows*5
Tags post in PatternDB.
Calls persona_patcher.py and mirofish_refiner.py.
"""

import os
from typing import List, Dict, Any
from datetime import datetime, timedelta
from logger import get_logger

logger = get_logger("feedback_loop.learning_engine")

# Persona path from env or default
PERSONA_PATH = os.getenv("PERSONA_PATH", "/data/personas/ahmad/persona.md")

# Trigger thresholds
MIN_POSTS_FOR_PATTERN = 3       # min posts per combo to draw conclusions
TIME_TRIGGER_DAYS = 14          # patch performance memory every 14 days
ENGAGEMENT_DROP_THRESHOLD = 0.20  # >20% drop over 5 consecutive posts
VOLUME_TRIGGER_POSTS = 30       # refresh every 30 posts


def compute_engagement_score(
    saves: float,
    shares: float,
    comments: float,
    follows: float,
    is_externally_amplified: bool = False,
    follower_count: int = 1,
    calendar_engagement_modifier: float = 1.0,
) -> float:
    """
    Exact scoring formula with follower normalization.
    Calendar-normalizes so holiday posts aren't unfairly penalized.
    """
    if is_externally_amplified:
        return 0.0  # Discard external viral outliers from learning loop

    followers = max(1, follower_count)
    saves_norm = (saves / followers) * 1000
    shares_norm = (shares / followers) * 1000
    comments_norm = (comments / followers) * 1000
    follows_norm = (follows / followers) * 1000

    raw_score = (saves_norm * 5) + (shares_norm * 3) + (comments_norm * 2) + (follows_norm * 5)

    # Normalize for calendar context (holiday posts score lower naturally)
    if calendar_engagement_modifier and calendar_engagement_modifier > 0:
        raw_score = raw_score / calendar_engagement_modifier

    return round(raw_score, 2)


def analyze_patterns(recent_posts: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analyze patterns across recent posts.
    Groups by hook_type + topic_pillar + format + account.
    Returns winning and underperforming combinations.
    """
    combinations = {}

    for post in recent_posts:
        account = post.get("account", "unknown")
        format_type = post.get("format", "unknown")
        pillar = post.get("topic_pillar", "unknown")
        hook = post.get("hook_type", "unknown")
        score = post.get("engagement_score", 0)

        key = (account, format_type, pillar, hook)
        if key not in combinations:
            combinations[key] = []
        combinations[key].append(score)

    winning = []
    underperforming = []

    # Compute dynamic baseline from all scores
    all_scores = [s for scores in combinations.values() for s in scores]
    baseline_score = sum(all_scores) / max(len(all_scores), 1) if all_scores else 50

    for key, scores in combinations.items():
        if len(scores) >= MIN_POSTS_FOR_PATTERN:
            avg_score = sum(scores) / len(scores)
            entry = {
                "account": key[0],
                "format": key[1],
                "topic_pillar": key[2],
                "hook_type": key[3],
                "avg_score": round(avg_score, 1),
                "count": len(scores),
            }
            if avg_score > baseline_score * 1.5:
                winning.append(entry)
            elif avg_score < baseline_score * 0.5:
                underperforming.append(entry)

    return {
        "winning_combinations": sorted(winning, key=lambda x: x["avg_score"], reverse=True),
        "underperforming_combinations": sorted(underperforming, key=lambda x: x["avg_score"]),
        "baseline_score": round(baseline_score, 1),
        "total_posts_analyzed": len(all_scores),
    }


def process_post_feedback(
    post_id: str,
    account: str,
    format_type: str,
    topic_pillar: str,
    hook_type: str,
    saves: int,
    shares: int,
    comments: int,
    follows: int,
    early_learning_signal: dict = None,
    follower_count: int = 1,
    calendar_engagement_modifier: float = 1.0,
    db_session=None,
) -> float:
    """
    Full feedback processing:
    1. Compute engagement score
    2. Write to PatternDB
    3. Check trigger conditions for persona/refiner updates
    """
    score = compute_engagement_score(
        saves, shares, comments, follows,
        follower_count=follower_count,
        calendar_engagement_modifier=calendar_engagement_modifier,
    )

    logger.info("Post feedback processed", extra={
        "post_id": post_id,
        "account": account,
        "engagement_score": score,
        "early_signal": bool(early_learning_signal),
    })

    # Write to PatternDB
    if db_session:
        _upsert_pattern_db(
            db_session, account, hook_type, topic_pillar, format_type, score
        )

    return score


def _upsert_pattern_db(db_session, account, hook_type, topic_pillar, format_type, score):
    """Insert or update PatternDB record for this combination."""
    try:
        from db.models import PatternDB

        existing = db_session.query(PatternDB).filter_by(
            account=account,
            pattern_name=f"{hook_type}|{topic_pillar}|{format_type}",
        ).first()

        if existing:
            # Running average
            old_count = existing.post_count or 0
            old_avg = existing.avg_normalized_score or 0
            new_count = old_count + 1
            new_avg = ((old_avg * old_count) + score) / new_count

            existing.avg_normalized_score = round(new_avg, 2)
            existing.post_count = new_count
            existing.last_updated = datetime.utcnow()
        else:
            record = PatternDB(
                account=account,
                pattern_name=f"{hook_type}|{topic_pillar}|{format_type}",
                sub_topic=topic_pillar,
                emotional_tone=hook_type,
                avg_normalized_score=score,
                post_count=1,
                last_updated=datetime.utcnow(),
            )
            db_session.add(record)

        db_session.commit()
        logger.info("PatternDB updated", extra={
            "account": account,
            "combo": f"{hook_type}|{topic_pillar}|{format_type}",
            "score": score,
        })
    except Exception as e:
        logger.error("PatternDB write failed", extra={"error": str(e)})
        db_session.rollback()


def run_weekly_learning_cycle(db_session) -> dict:
    """
    Full weekly learning cycle called by feedback_worker.
    1. Collect all posts from last 7 days with 48h+ data
    2. Compute patterns
    3. Check trigger conditions
    4. Call persona_patcher if triggers met
    5. Call mirofish_refiner with updated patterns
    """
    from db.models import Post, PostAnalytics

    # 1. Get posts from last 7 days that have analytics
    cutoff = datetime.utcnow() - timedelta(days=7)
    analytics_cutoff = datetime.utcnow() - timedelta(hours=48)

    posts = db_session.query(Post).filter(
        Post.published_at >= cutoff,
        Post.published_at <= analytics_cutoff,
        Post.analytics_collected == True,
    ).all()

    if not posts:
        logger.info("No posts with sufficient data for learning cycle")
        return {"posts_analyzed": 0, "patterns": {}, "patches_applied": False}

    # 2. Build post data list for pattern analysis
    post_data = []
    for post in posts:
        analytics = db_session.query(PostAnalytics).filter_by(post_id=post.id).first()
        if analytics:
            score = compute_engagement_score(
                saves=analytics.saves or 0,
                shares=analytics.shares or 0,
                comments=analytics.comments or 0,
                follows=analytics.follows or 0,
                follower_count=analytics.followers_at_post_time or 1,
                calendar_engagement_modifier=post.calendar_engagement_modifier or 1.0,
            )
            post_data.append({
                "post_id": post.id,
                "account": post.account,
                "format": post.format or "unknown",
                "topic_pillar": post.topic_pillar or "unknown",
                "hook_type": post.hook_type or "unknown",
                "engagement_score": score,
            })

            # Write score to PatternDB
            _upsert_pattern_db(
                db_session, post.account,
                post.hook_type or "unknown",
                post.topic_pillar or "unknown",
                post.format or "unknown",
                score,
            )

    # 3. Analyze patterns
    patterns = analyze_patterns(post_data)

    logger.info("Weekly patterns analyzed", extra={
        "posts_analyzed": len(post_data),
        "winning": len(patterns["winning_combinations"]),
        "underperforming": len(patterns["underperforming_combinations"]),
    })

    # 4. Check trigger conditions and call persona_patcher
    patches_applied = False
    trigger_type = _check_triggers(post_data, db_session)

    if trigger_type:
        try:
            from feedback_loop.persona_patcher import apply_persona_patches
            result = apply_persona_patches(
                persona_path=PERSONA_PATH,
                recent_patterns=patterns,
                total_posts=len(post_data),
                trigger_type=trigger_type,
            )
            patches_applied = result.get("success", False)
            logger.info("Persona patcher called", extra={
                "trigger": trigger_type,
                "result": result,
            })
        except Exception as e:
            logger.error("Persona patcher failed", extra={"error": str(e)})

    # 5. Call mirofish_refiner with updated patterns
    try:
        from feedback_loop.mirofish_refiner import refine_mirofish_signals
        refine_mirofish_signals(patterns)
        logger.info("MiroFish refiner called with updated patterns")
    except Exception as e:
        logger.error("MiroFish refiner failed", extra={"error": str(e)})

    return {
        "posts_analyzed": len(post_data),
        "patterns": patterns,
        "patches_applied": patches_applied,
        "trigger_type": trigger_type,
    }


def _check_triggers(post_data: list, db_session) -> str:
    """
    Check which update trigger is active.
    Returns trigger type or None.
    """
    if not post_data:
        return None

    # Check engagement drop: >20% drop over last 5 posts
    if len(post_data) >= 5:
        recent_5 = [p["engagement_score"] for p in post_data[-5:]]
        older_5 = [p["engagement_score"] for p in post_data[:5]]
        if older_5:
            recent_avg = sum(recent_5) / len(recent_5)
            older_avg = sum(older_5) / len(older_5)
            if older_avg > 0 and (older_avg - recent_avg) / older_avg > ENGAGEMENT_DROP_THRESHOLD:
                logger.warning("Engagement drop detected", extra={
                    "recent_avg": round(recent_avg, 1),
                    "older_avg": round(older_avg, 1),
                    "drop_pct": round((older_avg - recent_avg) / older_avg * 100, 1),
                })
                return "engagement_drop"

    # Check volume trigger
    try:
        from db.models import Post
        total_posts = db_session.query(Post).filter(
            Post.analytics_collected == True
        ).count()
        if total_posts > 0 and total_posts % VOLUME_TRIGGER_POSTS == 0:
            return "volume"
    except Exception:
        pass

    # Default: time-based (every 14 days)
    return "time_based"

"""
Oybit — Cold Start Bootstrap (GAP 6.6)
Seeds PatternDB from existing LinkedIn data for new accounts.
"""
import logging
from datetime import datetime
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

def bootstrap_from_linkedin(db: Session, linkedin_posts: list[dict]):
    """
    Seed PatternDB from existing LinkedIn post data.
    
    Args:
        db: database session
        linkedin_posts: list of dicts with {text, likes, comments, shares, impressions, published_at}
    """
    from db.models import PatternDB
    from utils.content_guards import normalize_engagement
    
    patterns = {}
    for post in linkedin_posts:
        # Detect hook type from text
        text = post.get("text", "")
        hook_type = detect_hook_type(text)
        
        score = normalize_engagement(
            post.get("likes", 0),
            post.get("comments", 0),
            post.get("shares", 0),
            post.get("saves", 0),
            post.get("followers", 1)
        )
        
        if hook_type not in patterns:
            patterns[hook_type] = {"scores": [], "count": 0}
        patterns[hook_type]["scores"].append(score)
        patterns[hook_type]["count"] += 1
    
    for hook, data in patterns.items():
        avg_score = sum(data["scores"]) / len(data["scores"]) if data["scores"] else 0
        pattern = PatternDB(
            account="linkedin",
            pattern_name=hook,
            trigger_conditions={"source": "bootstrap"},
            success_metric=avg_score,
            avg_normalized_score=avg_score,
            post_count=data["count"],
            last_updated=datetime.utcnow()
        )
        db.add(pattern)
    
    db.commit()
    logger.info({"event": "bootstrap_complete", "patterns_created": len(patterns)})

def detect_hook_type(text: str) -> str:
    """Simple hook type detector for bootstrapping."""
    text_lower = text.lower()
    if text_lower.startswith("how "):
        return "how_to"
    elif "?" in text[:50]:
        return "question"
    elif any(w in text_lower[:30] for w in ["myth", "wrong", "stop", "never"]):
        return "contrarian"
    elif any(w in text_lower[:30] for w in ["story", "years ago", "remember"]):
        return "story"
    elif any(char.isdigit() for char in text[:20]):
        return "listicle"
    else:
        return "statement"

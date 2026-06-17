"""
Oybit — Variation Enforcer (Agent A)
Ensures cross-platform variation so the same exact post isn't spammed to all 4 platforms simultaneously.
(GAPS_FINAL 6.1)
"""
from typing import List, Dict
from datetime import datetime, timedelta
from logger import get_logger

logger = get_logger("variation_enforcer")

def get_word_set(text: str) -> set:
    if not text:
        return set()
    # Simple keyword extraction, removing standard stopwords is better but this works for MVP
    words = text.lower().replace(".", "").replace(",", "").split()
    return set([w for w in words if len(w) > 3])

def calculate_similarity(text1: str, text2: str) -> float:
    """Calculates Jaccard similarity between two texts based on word sets."""
    set1 = get_word_set(text1)
    set2 = get_word_set(text2)
    
    if not set1 or not set2:
        return 0.0
        
    intersection = set1.intersection(set2)
    union = set1.union(set2)
    
    return len(intersection) / len(union)

def enforce_cross_platform_variation(candidates: List[Dict], threshold: float = 0.6) -> List[Dict]:
    """
    Takes a batch of generated candidates intended for different platforms.
    If two candidates are too similar (>60%), it drops the lower-scored one,
    forcing the system to generate a different angle for that platform later.
    """
    accepted = []
    
    # Sort candidates by score descending to prioritize keeping the best ones
    sorted_candidates = sorted(candidates, key=lambda c: c.get("score_total", 0), reverse=True)
    
    for candidate in sorted_candidates:
        text = candidate.get("content_text", "")
        platform = candidate.get("account", "unknown")
        
        is_too_similar = False
        for existing in accepted:
            sim = calculate_similarity(text, existing.get("content_text", ""))
            if sim > threshold:
                is_too_similar = True
                logger.info(f"Variation Enforcer dropped {platform} candidate. Too similar ({sim:.2f}) to {existing.get('account')}.")
                break
                
        if not is_too_similar:
            accepted.append(candidate)
            
    return accepted

def check_topic_exclusivity(topic: str, accounts: List[str], db_session, window_hours: int = 48) -> List[str]:
    """
    Checks if a given topic has been posted on any of the target accounts within the window.
    Returns the list of accounts where this topic is STILL allowed (i.e. hasn't been posted recently).
    """
    from db.models import Post
    
    allowed_accounts = []
    cutoff = datetime.utcnow() - timedelta(hours=window_hours)
    
    try:
        recent_posts = db_session.query(Post).filter(
            Post.created_at >= cutoff,
            Post.account.in_(accounts)
        ).all()
        
        # Build a map of account -> recent topics
        account_topics = {acc: [] for acc in accounts}
        for p in recent_posts:
            if p.content_text:  # Simple check, ideally we'd use embedded similarity
                account_topics[p.account].append(p.content_text.lower())
                
        topic_words = get_word_set(topic)
        
        for acc in accounts:
            is_exclusive = True
            for past_text in account_topics[acc]:
                sim = calculate_similarity(topic, past_text)
                if sim > 0.4:  # If topic words heavily match a past post
                    is_exclusive = False
                    logger.info(f"Topic '{topic}' excluded from {acc} (posted within {window_hours}h).")
                    break
                    
            if is_exclusive:
                allowed_accounts.append(acc)
                
        return allowed_accounts
        
    except Exception as e:
        logger.error(f"Failed topic exclusivity check: {e}")
        return accounts  # Fail open

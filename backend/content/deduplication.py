"""
Oybit — Duplicate Content Detector
Ensures we don't post semantic duplicates across a 30-post window.
(GAPS_AND_FIXES 6.2)
"""
from backend.logger import get_logger

logger = get_logger("deduplication")

def get_word_set(text: str) -> set:
    if not text:
        return set()
    words = text.lower().replace(".", "").replace(",", "").split()
    return set([w for w in words if len(w) > 4])  # Stricter word match for deduplication

def is_duplicate(new_text: str, recent_posts: list, threshold: float = 0.85) -> bool:
    """
    Checks if new_text is semantically a duplicate of any post in recent_posts.
    recent_posts should be a list of strings (the text of the last 30 posts).
    """
    if not new_text or not recent_posts:
        return False
        
    set_new = get_word_set(new_text)
    if not set_new:
        return False
        
    for past_text in recent_posts:
        if not past_text:
            continue
            
        set_past = get_word_set(past_text)
        if not set_past:
            continue
            
        intersection = set_new.intersection(set_past)
        union = set_new.union(set_past)
        
        sim = len(intersection) / len(union) if union else 0
        if sim >= threshold:
            logger.info(f"Duplicate content detected! Similarity: {sim:.2f}")
            return True
            
    return False

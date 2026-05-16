"""
Oybit — Voice Drift Detector
Compares Ahmad's manual posts against the persona.md voice to detect if his real voice is shifting.
(GAPS_FINAL 4.3)
"""
import re
import os
from datetime import datetime, timedelta
from typing import List, Dict
from backend.logger import get_logger

logger = get_logger("drift_detector")

def load_persona_keywords(persona_path: str) -> set:
    """Loads voice keywords from persona.md"""
    if not os.path.exists(persona_path):
        return set()
        
    try:
        with open(persona_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        match = re.search(r'Vocabulary always used:\*\*\s*(.*?)$', content, re.MULTILINE)
        if match:
            return set(w.strip().lower() for w in match.group(1).split(","))
    except Exception as e:
        logger.error(f"Error loading persona for drift detection: {e}")
        
    return set()


def extract_keywords(text: str) -> set:
    if not text:
        return set()
    words = re.findall(r'\b\w+\b', text.lower())
    # Extremely basic stopword filter for MVP
    stopwords = {"the", "a", "an", "and", "or", "but", "is", "are", "was", "were", "in", "on", "at", "to", "for"}
    return set(w for w in words if w not in stopwords and len(w) > 3)


def detect_voice_drift(db_session, persona_path: str, window_days: int = 14) -> Dict:
    """
    Analyzes Ahmad's manually published posts over the last N days.
    If his vocabulary differs significantly from the persona.md keywords, returns a drift warning.
    """
    from backend.db.models import Post
    
    cutoff = datetime.utcnow() - timedelta(days=window_days)
    
    # We assume manual posts are those without AI score fields, or marked manually
    recent_manual_posts = db_session.query(Post).filter(
        Post.created_at >= cutoff,
        Post.score_total.is_(None)  # proxy for manual posts
    ).all()
    
    if not recent_manual_posts:
        return {"drift_detected": False, "reason": "Not enough manual posts to establish baseline."}
        
    persona_keywords = load_persona_keywords(persona_path)
    if not persona_keywords:
        return {"drift_detected": False, "reason": "Persona keyword list is empty."}
        
    # Extract common keywords from his real posts
    all_real_words = []
    for p in recent_manual_posts:
        if p.content_text:
            all_real_words.extend(list(extract_keywords(p.content_text)))
            
    if not all_real_words:
        return {"drift_detected": False, "reason": "No text content in recent manual posts."}
        
    # Get top 20 real words
    word_counts = {}
    for w in all_real_words:
        word_counts[w] = word_counts.get(w, 0) + 1
        
    top_real_words = set(sorted(word_counts, key=word_counts.get, reverse=True)[:20])
    
    # Calculate overlap
    intersection = persona_keywords.intersection(top_real_words)
    overlap_ratio = len(intersection) / len(persona_keywords) if persona_keywords else 0
    
    drift_detected = overlap_ratio < 0.2  # Less than 20% of his core voice words showed up in recent real posts
    
    result = {
        "drift_detected": drift_detected,
        "overlap_ratio": overlap_ratio,
        "missing_keywords": list(persona_keywords - intersection),
        "new_emerging_keywords": list(top_real_words - persona_keywords)[:5],
        "reason": f"Overlap ratio {overlap_ratio:.2f} is below 0.2 threshold." if drift_detected else "Voice aligned."
    }
    
    if drift_detected:
        logger.warning(f"Voice drift detected! Missing: {result['missing_keywords']}")
        # In a full system, this would trigger a notification to Ahmad asking if he wants to update the persona.
        
    return result

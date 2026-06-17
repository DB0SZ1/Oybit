"""
Oybit — Voice Drift Detector (GAP 4.3)
Monitors published posts over time to ensure the system's voice isn't
slowly drifting away from Ahmad's original persona.
"""

import logging
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from db.models import Post
from guardian.checker import _load_persona_data, _compute_tone_similarity
from alerts.telegram import send_alert

logger = logging.getLogger(__name__)

def detect_voice_drift(db: Session, persona_path: str) -> dict:
    """
    Analyze the last 7 days of published posts to detect voice drift.
    Returns a drift report and alerts if drift is severe.
    """
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    
    # Get recent published posts
    recent_posts = db.query(Post).filter(
        Post.status == "published",
        Post.created_at >= seven_days_ago
    ).all()
    
    if len(recent_posts) < 5:
        return {"status": "insufficient_data", "post_count": len(recent_posts)}
        
    persona_data = _load_persona_data(persona_path)
    voice_keywords = persona_data.get("voice_keywords", [])
    anti_voice = persona_data.get("anti_voice", [])
    
    if not voice_keywords:
        return {"status": "no_persona_data"}
        
    scores = []
    for p in recent_posts:
        if p.content_text:
            score = _compute_tone_similarity(p.content_text, voice_keywords, anti_voice)
            scores.append(score)
            
    avg_score = sum(scores) / len(scores)
    
    # Threshold for drift: if average tone similarity drops below 0.60
    is_drifting = avg_score < 0.60
    
    report = {
        "status": "drift_detected" if is_drifting else "voice_stable",
        "post_count": len(recent_posts),
        "average_tone_score": avg_score,
        "is_drifting": is_drifting
    }
    
    if is_drifting:
        logger.warning(f"Voice drift detected! Average score: {avg_score:.2f}")
        send_alert(f"⚠️ *Voice Drift Detected!*\nThe average tone score for the last 7 days is critically low ({avg_score:.2f}).\nThe AI might be losing your personal voice. Check the persona settings.", "WARNING")
        
    return report

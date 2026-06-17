"""
Oybit — Persona & Content Intelligence (GAPS_FINAL GAPs 4.1–4.4)
Whisper transcription, Nyvora webhooks, voice drift detection, Nigerian cultural calendar.
"""
import logging
import os
import json
from datetime import datetime, date
from pathlib import Path

logger = logging.getLogger(__name__)

# ── GAP 4.1: Whisper Vlog Transcription ───────────────────────
def transcribe_vlog(audio_path: str) -> str:
    """
    Transcribe a vlog/voice note using OpenAI Whisper API.
    The transcription feeds into persona updates and content ideas.
    """
    import httpx
    
    api_key = os.getenv("OPENAI_API_KEY", "")
    if not api_key:
        logger.warning({"event": "whisper_no_api_key"})
        return ""
    
    try:
        with open(audio_path, 'rb') as f:
            resp = httpx.post(
                "https://api.openai.com/v1/audio/transcriptions",
                headers={"Authorization": f"Bearer {api_key}"},
                files={"file": (Path(audio_path).name, f, "audio/mpeg")},
                data={"model": "whisper-1", "language": "en"},
                timeout=120
            )
        
        if resp.status_code == 200:
            text = resp.json().get("text", "")
            logger.info({"event": "vlog_transcribed", "chars": len(text)})
            return text
        else:
            logger.error({"event": "whisper_failed", "status": resp.status_code})
            return ""
    except Exception as e:
        logger.error({"event": "whisper_error", "error": str(e)})
        return ""


# ── GAP 4.2: Nyvora Product Event Webhooks ────────────────────
def process_nyvora_webhook(event_data: dict) -> dict:
    """Process incoming Nyvora product events for content triggers."""
    event_type = event_data.get("type", "")
    
    content_triggers = {
        "product_launch": "New product announcement content",
        "milestone": "Celebration/milestone content",
        "feature_update": "Feature highlight content",
        "user_testimonial": "Social proof content",
        "partnership": "Partnership announcement content"
    }
    
    trigger = content_triggers.get(event_type)
    if trigger:
        return {
            "should_generate": True,
            "content_type": trigger,
            "event_data": event_data,
            "priority": "high" if event_type in ("product_launch", "partnership") else "normal"
        }
    
    return {"should_generate": False, "reason": f"Unknown event type: {event_type}"}


# ── GAP 4.3: Voice Drift Detection ────────────────────────────
def detect_voice_drift(recent_posts: list[str], persona_voice_markers: list[str]) -> dict:
    """
    Check if recent content has drifted from Ahmad's established voice.
    Compares keyword/phrase frequency against persona baseline.
    """
    # Count marker presence in recent posts
    total_posts = len(recent_posts)
    if total_posts == 0:
        return {"drift_detected": False, "score": 0}
    
    marker_hits = 0
    total_markers = len(persona_voice_markers)
    
    for post in recent_posts:
        post_lower = post.lower()
        for marker in persona_voice_markers:
            if marker.lower() in post_lower:
                marker_hits += 1
    
    # Calculate drift score (0 = perfect alignment, 100 = complete drift)
    expected_hits = total_markers * total_posts * 0.3  # Expect 30% marker presence
    actual_ratio = marker_hits / max(expected_hits, 1)
    drift_score = max(0, min(100, round((1 - actual_ratio) * 100)))
    
    return {
        "drift_detected": drift_score > 60,
        "drift_score": drift_score,
        "marker_hits": marker_hits,
        "recommendation": "Review persona.md and recent content" if drift_score > 60 else "Voice consistent"
    }


# ── GAP 4.4: Nigerian Public Holidays & Cultural Calendar ─────
NIGERIAN_HOLIDAYS_2026 = {
    "2026-01-01": {"name": "New Year's Day", "tone": "celebration"},
    "2026-03-20": {"name": "Eid al-Fitr (tentative)", "tone": "celebration"},
    "2026-04-03": {"name": "Good Friday", "tone": "reflective"},
    "2026-04-06": {"name": "Easter Monday", "tone": "celebration"},
    "2026-05-01": {"name": "Workers' Day", "tone": "appreciation"},
    "2026-05-27": {"name": "Eid al-Adha (tentative)", "tone": "celebration"},
    "2026-06-12": {"name": "Democracy Day", "tone": "patriotic"},
    "2026-10-01": {"name": "Independence Day", "tone": "patriotic"},
    "2026-12-25": {"name": "Christmas Day", "tone": "celebration"},
    "2026-12-26": {"name": "Boxing Day", "tone": "celebration"},
}

# Major Nigerian tech/business events
NIGERIAN_EVENTS_2026 = {
    "2026-02-01": {"name": "Lagos Tech Summit", "relevance": "high"},
    "2026-07-01": {"name": "AfriLabs Annual Gathering", "relevance": "medium"},
    "2026-09-01": {"name": "Lagos Startup Week", "relevance": "high"},
    "2026-11-01": {"name": "Gitex Africa", "relevance": "medium"},
}

def get_today_context() -> dict:
    """Get cultural context for today's content decisions."""
    today = date.today().isoformat()
    
    result = {"date": today, "is_holiday": False, "holiday": None, "upcoming_events": []}
    
    if today in NIGERIAN_HOLIDAYS_2026:
        result["is_holiday"] = True
        result["holiday"] = NIGERIAN_HOLIDAYS_2026[today]
    
    # Check upcoming events (within 7 days)
    from datetime import timedelta
    for i in range(7):
        check_date = (date.today() + timedelta(days=i)).isoformat()
        if check_date in NIGERIAN_EVENTS_2026:
            result["upcoming_events"].append({
                "days_away": i,
                **NIGERIAN_EVENTS_2026[check_date]
            })
    
    return result

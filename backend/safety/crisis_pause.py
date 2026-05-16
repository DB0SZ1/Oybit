"""
Oybit — Tragedy & Crisis Pause (GAP 10.1)
Detects sensitive moments and pauses all automated posting.
"""
import httpx
import logging
import os
import json
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

PAUSE_FILE = Path(os.getenv("PAUSE_FILE_PATH", "/data/pause_posting.flag"))

# Nigerian-specific sensitive topics
SENSITIVE_KEYWORDS = [
    "massacre", "bombing", "terror attack", "mass shooting",
    "national mourning", "plane crash", "building collapse",
    "fuel tanker explosion", "boat sinking", "kidnapping crisis",
    "election violence", "protest shooting", "stampede",
    "RIP", "tragedy", "disaster", "breaking news",
]

def check_for_crisis(news_text: str = "") -> bool:
    """Check if current events warrant a posting pause."""
    text_lower = news_text.lower()
    for keyword in SENSITIVE_KEYWORDS:
        if keyword.lower() in text_lower:
            logger.warning({"event": "crisis_detected", "keyword": keyword})
            return True
    return False

def activate_pause(reason: str, duration_hours: int = 24):
    """Activate the posting pause flag."""
    PAUSE_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    pause_data = {
        "activated_at": datetime.utcnow().isoformat() + "Z",
        "reason": reason,
        "duration_hours": duration_hours,
        "activated_by": "crisis_detector"
    }
    PAUSE_FILE.write_text(json.dumps(pause_data), encoding='utf-8')
    logger.warning({"event": "posting_paused", "reason": reason, "hours": duration_hours})

def deactivate_pause():
    """Remove the posting pause flag."""
    if PAUSE_FILE.exists():
        PAUSE_FILE.unlink()
        logger.info({"event": "posting_resumed"})

def is_paused() -> bool:
    """Check if posting is currently paused."""
    if not PAUSE_FILE.exists():
        return False
    
    try:
        data = json.loads(PAUSE_FILE.read_text('utf-8'))
        activated_at = datetime.fromisoformat(data["activated_at"].rstrip("Z"))
        from datetime import timedelta
        expires_at = activated_at + timedelta(hours=data.get("duration_hours", 24))
        
        if datetime.utcnow() > expires_at:
            deactivate_pause()
            return False
        return True
    except Exception:
        return True  # If we can't parse, assume paused for safety

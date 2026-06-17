"""
Oybit — Real Event Ingestion (GAP 7.7 — The Authenticity Gap)
Ingests Ahmad's real-life events via Telegram webhook or manual input
so Oybit can incorporate real moments into content.
"""
import json
import logging
import os
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

EVENT_LOG_PATH = Path(os.getenv("EVENT_LOG_PATH", "/data/events/events.jsonl"))

def ingest_event(event_text: str, event_type: str = "general",
                  source: str = "manual") -> dict:
    """
    Record a real-life event for inclusion in future content.
    
    Args:
        event_text: What happened (e.g. "Just landed in Lagos for the conference")
        event_type: Category: "general", "travel", "meeting", "achievement", "product", "personal"
        source: How it was submitted: "manual", "telegram", "webhook"
    """
    EVENT_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "event_type": event_type,
        "text": event_text,
        "source": source,
        "used": False,  # Marks whether content has been generated from this
        "content_refs": []  # Post IDs that used this event
    }
    
    with open(EVENT_LOG_PATH, 'a', encoding='utf-8') as f:
        f.write(json.dumps(entry) + '\n')
    
    logger.info({"event": "event_ingested", "type": event_type, "source": source})
    return entry

def get_unused_events(max_age_hours: int = 72) -> list[dict]:
    """Get recent events that haven't been used in content yet."""
    if not EVENT_LOG_PATH.exists():
        return []
    
    events = []
    cutoff = datetime.utcnow().timestamp() - (max_age_hours * 3600)
    
    with open(EVENT_LOG_PATH, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            entry = json.loads(line)
            if not entry.get("used"):
                ts = datetime.fromisoformat(entry["timestamp"].rstrip("Z")).timestamp()
                if ts > cutoff:
                    events.append(entry)
    
    return events

def mark_event_used(event_timestamp: str, post_id: int):
    """Mark an event as used by a particular post."""
    if not EVENT_LOG_PATH.exists():
        return
    
    lines = EVENT_LOG_PATH.read_text('utf-8').strip().split('\n')
    updated = []
    for line in lines:
        if not line:
            continue
        entry = json.loads(line)
        if entry.get("timestamp") == event_timestamp:
            entry["used"] = True
            entry["content_refs"].append(post_id)
        updated.append(json.dumps(entry))
    
    EVENT_LOG_PATH.write_text('\n'.join(updated) + '\n', encoding='utf-8')

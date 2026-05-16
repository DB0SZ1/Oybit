"""
Telegram Event Listener — Ahmad sends real events via Telegram,
Oybit creates high-priority content briefs that bypass MiroFish.

Real events (shipping moments, first customer, 3AM debugging) always
outperform AI-predicted narratives. This is the authenticity channel.
"""

import os
import json
from datetime import datetime
from backend.content.generator import call_openrouter_raw
from backend.logger import get_logger

logger = get_logger("event_ingestion.telegram_listener")

AHMAD_CHAT_ID = os.getenv("TELEGRAM_AHMAD_CHAT_ID", "")


def is_authorized(chat_id: str) -> bool:
    """Only Ahmad can trigger real event ingestion."""
    return str(chat_id) == AHMAD_CHAT_ID and AHMAD_CHAT_ID != ""


def expand_real_event(raw_event: str) -> dict:
    """
    Expand a raw event message into a structured content brief.
    E.g., "just shipped the pre-publish gate, 3am, took way longer than expected"
    → structured brief with hook, angle, platform recommendations

    Args:
        raw_event: Ahmad's raw message text

    Returns:
        Structured content brief dict
    """
    prompt = (
        f"Ahmad is a Nigerian developer/founder who builds in public. "
        f"He just sent this real-time update:\n\n"
        f'"{raw_event}"\n\n'
        f"Turn this into 3 content briefs for different platforms (LinkedIn, Instagram, Facebook).\n"
        f"Each brief should capture the raw authenticity of the moment.\n"
        f"Return ONLY valid JSON:\n"
        f'{{"briefs": [\n'
        f'  {{"platform": "linkedin", "hook": "...", "angle": "...", '
        f'"format": "text|carousel", "key_points": ["..."], "emotion": "..."}}\n'
        f"]}}"
    )

    try:
        result = call_openrouter_raw(prompt, max_tokens=500)
        cleaned = result.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[1]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]

        data = json.loads(cleaned)
        briefs = data.get("briefs", [])

        logger.info("Real event expanded", extra={
            "event_preview": raw_event[:50],
            "briefs_count": len(briefs),
        })
        return {
            "source": "real_event",
            "priority": "high",
            "raw_event": raw_event,
            "timestamp": datetime.utcnow().isoformat(),
            "bypass_mirofish": True,
            "briefs": briefs,
        }

    except Exception as e:
        logger.error("Event expansion failed", extra={"error": str(e)})
        # Return a basic brief even if AI fails
        return {
            "source": "real_event",
            "priority": "high",
            "raw_event": raw_event,
            "timestamp": datetime.utcnow().isoformat(),
            "bypass_mirofish": True,
            "briefs": [{
                "platform": "linkedin",
                "hook": raw_event[:100],
                "angle": "Building in public",
                "format": "text",
                "key_points": [raw_event],
                "emotion": "authentic",
            }],
        }


def process_telegram_message(chat_id: str, message_text: str) -> dict:
    """
    Process an incoming Telegram message from Ahmad.

    Args:
        chat_id: Telegram chat ID of the sender
        message_text: the message text

    Returns:
        dict with processing result
    """
    if not is_authorized(chat_id):
        logger.warning("Unauthorized Telegram message", extra={"chat_id": chat_id})
        return {"success": False, "error": "Unauthorized"}

    if not message_text or len(message_text.strip()) < 5:
        return {"success": False, "error": "Message too short"}

    # Expand the event into content briefs
    event_data = expand_real_event(message_text)

    logger.info("Real event ingested from Telegram", extra={
        "event_preview": message_text[:50],
        "briefs": len(event_data["briefs"]),
    })

    return {
        "success": True,
        "event_data": event_data,
        "reply_text": (
            f"Got it. Generated {len(event_data['briefs'])} content briefs "
            f"from your real moment — they'll be in the approval queue shortly."
        ),
    }

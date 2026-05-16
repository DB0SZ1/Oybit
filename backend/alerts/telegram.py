"""
Oybit — Telegram Self-Alert System (GAP 11.1)
Sends critical alerts to Ahmad via Telegram bot.
"""
import httpx
import logging
import os

logger = logging.getLogger(__name__)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

def send_alert(message: str, level: str = "INFO") -> bool:
    """
    Send an alert to Ahmad's Telegram.
    
    Args:
        message: Alert text
        level: INFO, WARNING, CRITICAL
    """
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logger.warning({"event": "telegram_not_configured"})
        return False
    
    emoji_map = {
        "INFO": "ℹ️",
        "WARNING": "⚠️",
        "CRITICAL": "🚨",
        "SUCCESS": "✅",
        "ERROR": "❌"
    }
    
    emoji = emoji_map.get(level, "📢")
    formatted = f"{emoji} *Oybit Alert [{level}]*\n\n{message}"
    
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": formatted,
        "parse_mode": "Markdown"
    }
    
    try:
        resp = httpx.post(url, json=payload, timeout=10)
        if resp.status_code == 200:
            logger.info({"event": "telegram_alert_sent", "level": level})
            return True
        else:
            logger.error({"event": "telegram_alert_failed", "status": resp.status_code})
            return False
    except Exception as e:
        logger.error({"event": "telegram_alert_error", "error": str(e)})
        return False

def alert_token_expiry(platform: str, hours_remaining: int):
    send_alert(f"Token for *{platform}* expires in {hours_remaining} hours. Refresh needed.", "WARNING")

def alert_publish_failure(account: str, post_id: int, error: str):
    send_alert(f"Failed to publish post #{post_id} to *{account}*:\n`{error}`", "ERROR")

def alert_crisis_pause(reason: str):
    send_alert(f"Posting paused due to crisis detection:\n_{reason}_", "CRITICAL")

def alert_daily_summary(posts_published: int, total_engagement: int):
    send_alert(f"Daily summary: {posts_published} posts published, {total_engagement} total engagement", "SUCCESS")

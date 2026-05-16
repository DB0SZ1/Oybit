"""
Oybit — Telegram Alerter
Sends system alerts (token expiry, bot bans, critical errors) to Ahmad.
(GAPS_AND_FIXES 10.3 / OYBIT_GAP_SOLUTIONS 9.1)
"""
import os
import requests
from backend.logger import get_logger

logger = get_logger("telegram_alerter")

def send_telegram_alert(message: str, urgency: str = "medium"):
    """
    Sends an alert to Ahmad's Telegram chat.
    Requires TELEGRAM_BOT_TOKEN and TELEGRAM_AHMAD_CHAT_ID env vars.
    """
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_AHMAD_CHAT_ID")
    
    if not bot_token or not chat_id:
        logger.warning("Telegram credentials missing, skipping alert.")
        return False
        
    emoji = "🔴" if urgency == "high" else "🟡" if urgency == "medium" else "ℹ️"
    full_message = f"{emoji} <b>Oybit Alert</b>\n\n{message}"
    
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": full_message,
        "parse_mode": "HTML"
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        return True
    except Exception as e:
        logger.error(f"Failed to send Telegram alert: {e}")
        return False

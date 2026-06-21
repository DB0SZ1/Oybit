"""
Oybit — Telegram Notifier Publisher
Sends Telegram messages instead of auto-publishing to platforms.
"""

import os
import logging
import requests

logger = logging.getLogger("telegram_notifier")

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_telegram_notification(post_id: str, account: str, content_text: str, dry_run: bool = False) -> dict:
    """
    Sends a Telegram notification to the user to manually post the content.
    Returns standard dispatcher result dict.
    """
    logger.info(f"Sending Telegram notification for post {post_id} on {account}")

    if dry_run:
        logger.info(f"DRY RUN: Would have sent Telegram to {TELEGRAM_CHAT_ID} for {account}")
        return {account: {"success": True, "dry_run": True, "message_sid": "DRY_RUN_SID"}}

    if not all([TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID]):
        error_msg = "Telegram credentials missing. Please set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID."
        logger.error(error_msg)
        return {account: {"success": False, "error": error_msg}}

    try:
        message_body = f"🚀 *OYBIT ALERT* | Time to post to *{account.upper()}*!\n\n"
        message_body += f"Copy the text below:\n---\n{content_text}\n---\n"
        
        # Telegram max length is 4096 characters, well beyond typical social posts
        if len(message_body) > 4000:
            message_body = message_body[:4000] + "...\n(truncated)"

        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message_body,
            "parse_mode": "Markdown"
        }

        resp = requests.post(url, json=payload, timeout=15)
        resp.raise_for_status()
        
        logger.info(f"Telegram message sent successfully for post {post_id}")
        return {account: {"success": True, "message_sid": f"telegram_{post_id}"}}

    except Exception as e:
        logger.error(f"Failed to send Telegram message: {e}")
        return {account: {"success": False, "error": str(e)}}

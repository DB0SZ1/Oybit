"""
Oybit — Twilio SMS Notifier Publisher
Sends SMS via Twilio instead of auto-publishing to platforms.
"""

import os
import logging
from twilio.rest import Client

logger = logging.getLogger("twilio_notifier")

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")
USER_PHONE_NUMBER = os.getenv("USER_PHONE_NUMBER")

def send_twilio_notification(post_id: str, account: str, content_text: str, dry_run: bool = False) -> dict:
    """
    Sends an SMS notification to the user to manually post the content.
    Returns standard dispatcher result dict.
    """
    logger.info(f"Sending Twilio notification for post {post_id} on {account}")

    if dry_run:
        logger.info(f"DRY RUN: Would have texted {USER_PHONE_NUMBER} for {account}")
        return {account: {"success": True, "dry_run": True, "message_sid": "DRY_RUN_SID"}}

    if not all([TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER, USER_PHONE_NUMBER]):
        error_msg = "Twilio credentials missing. Please set TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER, and USER_PHONE_NUMBER."
        logger.error(error_msg)
        return {account: {"success": False, "error": error_msg}}

    try:
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        
        message_body = f"[OYBIT ALERT] ⏰ Time to post to {account.upper()}!\n\n"
        message_body += f"Copy the text below:\n---\n{content_text}\n---\n"
        
        # Twilio SMS max length is 1600 characters
        if len(message_body) > 1550:
            message_body = message_body[:1550] + "...\n(truncated)"

        # Handle WhatsApp Sandbox automatically
        from_number = TWILIO_PHONE_NUMBER
        to_number = USER_PHONE_NUMBER
        if from_number == "+14155238886":
            from_number = f"whatsapp:{from_number}"
            to_number = f"whatsapp:{to_number}"

        message = client.messages.create(
            body=message_body,
            from_=from_number,
            to=to_number
        )
        
        logger.info(f"Twilio message sent successfully: {message.sid}")
        return {account: {"success": True, "message_sid": message.sid}}

    except Exception as e:
        logger.error(f"Failed to send Twilio SMS: {e}")
        return {account: {"success": False, "error": str(e)}}

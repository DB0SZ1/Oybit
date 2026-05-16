"""
Oybit — External Events API
Listens for Nyvora webhooks (commits, deployments) to trigger content generation.
(GAPS_AND_FIXES 10.1)
"""
import os
import hmac
import hashlib
from fastapi import APIRouter, Header, HTTPException, Request, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from backend.logger import get_logger
from backend.api.schemas import NyvoraWebhookPayload
from backend.db.session import get_db
from backend.event_ingestion.telegram_listener import process_telegram_message
from backend.api.pipeline import step_generate
from backend.alerts.telegram import send_alert

router = APIRouter(prefix="/api/webhooks", tags=["webhooks"])
logger = get_logger("external_events")

def verify_nyvora_signature(payload_body: bytes, signature: str):
    secret = os.getenv("NYVORA_INTERNAL_WEBHOOK_SECRET", "")
    if not secret:
        return False
    expected = hmac.new(secret.encode(), payload_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(f"sha256={expected}", signature)

@router.post("/nyvora")
async def handle_nyvora_webhook(
    request: Request,
    payload: NyvoraWebhookPayload,
    x_nyvora_signature: str = Header(None)
):
    if not x_nyvora_signature:
        raise HTTPException(status_code=401, detail="Missing signature")
        
    body = await request.body()
    if not verify_nyvora_signature(body, x_nyvora_signature):
        raise HTTPException(status_code=401, detail="Invalid signature")
        
    logger.info(f"Received verified Nyvora webhook: {payload.event} for project {payload.project}")
    
    # In a full system, this would write to an Event table or message queue for workers
    return {"status": "accepted", "event": payload.event}

def _background_generate_from_event(db: Session, event_data: dict):
    """Background task to generate content from real event briefs."""
    try:
        raw_event = event_data.get("raw_event", "")
        for brief in event_data.get("briefs", []):
            topic_brief = f"REAL EVENT: {raw_event}\n\nPlatform Focus: {brief.get('platform')}\nHook: {brief.get('hook')}\nAngle: {brief.get('angle')}"
            step_generate(
                db=db,
                topic_brief=topic_brief,
                platform=brief.get("platform", "linkedin"),
                account=brief.get("platform", "linkedin"),
                format_type=brief.get("format", "text"),
                dry_run=False
            )
        send_alert(f"✅ Generated {len(event_data.get('briefs', []))} post variants from your real event update.", "SUCCESS")
    except Exception as e:
        logger.error(f"Background generation failed: {e}")
        send_alert(f"❌ Failed to generate from your real event: {e}", "ERROR")

@router.post("/telegram")
async def handle_telegram_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Webhook endpoint for Telegram bot. Processes messages from Ahmad."""
    try:
        data = await request.json()
        
        # Extract message info
        message = data.get("message", {})
        chat_id = str(message.get("chat", {}).get("id", ""))
        text = message.get("text", "")
        
        if not chat_id or not text:
            return {"status": "ignored", "reason": "no text or chat_id"}
            
        result = process_telegram_message(chat_id, text)
        
        if result.get("success"):
            # Trigger generation in background
            background_tasks.add_task(_background_generate_from_event, db, result["event_data"])
            
            # Send immediate reply back via Telegram API (optional, we also send_alert on complete)
            # send_alert(result["reply_text"], "INFO")
            
            return {"status": "accepted", "reply": result["reply_text"]}
        else:
            return {"status": "rejected", "error": result.get("error")}
            
    except Exception as e:
        logger.error(f"Telegram webhook error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

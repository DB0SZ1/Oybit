import os
import re
import json
import logging
import requests
from fastapi import APIRouter, Request, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from db.session import get_db
from db.models import Post, AuditLog
from services.llm import generate_build_in_public_post

logger = logging.getLogger("webhooks")
router = APIRouter(prefix="/api/webhooks", tags=["Webhooks"])

def _parse_latest_build_log() -> dict:
    """
    Parses the linkedin/BUILD_LOG.md file to extract the most recent entry.
    Format expected:
    ## [2026-06-06] - Feature Name
    **Images**: https://res.cloudinary.com/..., https://res.cloudinary.com/...
    **Tags**: #AI #Feature
    **Details**:
    Added the new webhook receiver and parsed the readme...
    """
    log_path = os.path.join(os.getcwd(), "BUILD_LOG.md")
    if not os.path.exists(log_path):
        # Fallback to README.md if BUILD_LOG doesn't exist
        log_path = os.path.join(os.getcwd(), "README.md")
        if not os.path.exists(log_path):
            return None

    with open(log_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Find the first Markdown heading 2 (## [Date] - Title)
    entries = re.split(r'(?m)^##\s+', content)
    if len(entries) < 2:
        return None  # No valid entries found
        
    latest_entry_raw = entries[1] # entries[0] is the content before the first ## 
    
    # Extract Title/Date (the first line)
    lines = latest_entry_raw.strip().split("\n")
    title = lines[0].strip()
    
    # Extract Images
    images = []
    images_match = re.search(r'\*\*Images\*\*:\s*(.*)', latest_entry_raw, re.IGNORECASE)
    if images_match:
        urls = images_match.group(1).split(",")
        images = [url.strip() for url in urls if "http" in url]
        
    # Extract Tags
    tags = []
    tags_match = re.search(r'\*\*Tags\*\*:\s*(.*)', latest_entry_raw, re.IGNORECASE)
    if tags_match:
        tags = [tag.strip() for tag in tags_match.group(1).split() if tag.strip().startswith("#")]
        
    # Extract the details (everything else)
    details = re.sub(r'(?m)^(\*\*Images\*\*|\*\*Tags\*\*):.*$', '', latest_entry_raw, flags=re.IGNORECASE)
    # Remove the first line (title)
    details = "\n".join(details.strip().split("\n")[1:]).strip()

    return {
        "title": title,
        "images": images,
        "tags": tags,
        "details": details
    }


@router.post("/github")
async def github_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Receives push events from GitHub.
    Since we shifted to local Git Hooks and daily batching, this webhook no longer generates posts immediately.
    Instead, it just acknowledges the push (or could be used to trigger a server-side git pull).
    """
    payload = await request.json()
    
    if "commits" not in payload:
        return {"status": "ignored", "reason": "Not a push event with commits"}
        
    logger.info(f"Received GitHub webhook push with {len(payload['commits'])} commits.")
    
    return {"status": "success", "message": "Push acknowledged. Progress is batched and will be picked up by bip_scheduler."}

from pydantic import BaseModel
class BuildLogPayload(BaseModel):
    summary: str

from fastapi import BackgroundTasks

@router.post("/build-log")
async def build_log_webhook(payload: BuildLogPayload, request: Request, background_tasks: BackgroundTasks):
    """
    Receives sanitized build log entries from remote standalone_watcher.py scripts.
    """
    # Removed authorization check since it's just us
    # secret = request.headers.get("Authorization")
    # expected_secret = f"Bearer {os.getenv('NYVORA_INTERNAL_WEBHOOK_SECRET', 'test_secret')}"
    # if not secret or secret != expected_secret:
    #     raise HTTPException(status_code=401, detail="Unauthorized")
        
    import datetime
    date_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    entry = f"## [{date_str}] - Remote Auto Commit\n"
    entry += "**Tags**: #BuildInPublic #Engineering\n"
    entry += "**Details**:\n"
    entry += f"{payload.summary}\n\n"
    
    from db.session import SessionLocal
    from db.models import BuildLogEntry

    db = SessionLocal()
    try:
        new_entry = BuildLogEntry(summary=entry, status="unposted")
        db.add(new_entry)
        db.commit()
    except Exception as e:
        logger.error(f"Failed to save webhook to DB: {e}")
        db.rollback()
        raise
    finally:
        db.close()
        
    # Trigger the LLM generator immediately in the background instead of waiting for the schedule!
    from workers.bip_scheduler import run_bip_batch_cycle
    background_tasks.add_task(run_bip_batch_cycle)
    
    return {"status": "success", "message": "Build log appended to database. LLM has been triggered in the background to generate posts."}

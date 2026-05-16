"""
Oybit — Waitlist API
Captures waitlist signups to database.
(GAPS_AND_FIXES 1.5)
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.db.session import get_db
from backend.db.models import WaitlistEntry
from backend.api.schemas import WaitlistEntryCreate
from backend.logger import get_logger

router = APIRouter(prefix="/api/waitlist", tags=["waitlist"])
logger = get_logger("waitlist_api")

@router.post("/")
def join_waitlist(entry: WaitlistEntryCreate, db: Session = Depends(get_db)):
    try:
        # Check if email exists
        existing = db.query(WaitlistEntry).filter(WaitlistEntry.email == entry.email).first()
        if existing:
            return {"status": "success", "message": "Email already on waitlist."}
            
        new_entry = WaitlistEntry(
            name=entry.name,
            email=entry.email,
            why_interested=entry.why_interested,
            source=entry.source
        )
        db.add(new_entry)
        db.commit()
        return {"status": "success", "message": "Joined waitlist successfully."}
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to join waitlist: {e}")
        raise HTTPException(status_code=500, detail="Failed to process waitlist entry")

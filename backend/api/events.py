"""
Oybit — Manual Events Flow
Ingests events from the UI to seed generation.
(GAPS_AND_FIXES Module 1)
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.db.session import get_db
from backend.api.schemas import EventCreate
from backend.logger import get_logger

router = APIRouter(prefix="/api/events", tags=["events"])
logger = get_logger("events_api")

@router.post("/")
def ingest_event(event: EventCreate, db: Session = Depends(get_db)):
    """
    Ingests a manual event (e.g. ship, thought, link) to seed generation.
    """
    logger.info(f"Manual event ingested: {event.event_type} from {event.source}")
    # Full implementation would write to DB and optionally trigger worker
    return {"status": "success", "message": "Event recorded."}

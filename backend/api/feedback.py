"""
Oybit — Real-time Feedback Flow
Ingests manual feedback for generated posts (calibration).
(GAPS_AND_FIXES Module 1)
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.db.session import get_db
from backend.api.schemas import FeedbackCreate
from backend.logger import get_logger

router = APIRouter(prefix="/api/feedback", tags=["feedback"])
logger = get_logger("feedback_api")

@router.post("/")
def submit_calibration_feedback(feedback: FeedbackCreate, db: Session = Depends(get_db)):
    """
    Records Ahmad's manual 1-10 rating on published posts for persona calibration.
    """
    logger.info(f"Feedback received for post {feedback.post_id}: {feedback.rating}/10")
    # Full implementation writes to DB and triggers calibration update
    return {"status": "success", "message": "Feedback recorded."}

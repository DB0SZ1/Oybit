import logging
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.db.session import get_db
from backend.db.models import OnboardingSession
from backend.api.auth import get_current_user
from backend.onboarding.questions import get_questions_for_stage, get_stage_info, get_total_question_count

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/onboarding", tags=["onboarding"])


@router.get("/session")
def get_or_create_onboarding_session(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    """Get the current onboarding session or create a new one."""
    session = db.query(OnboardingSession).order_by(OnboardingSession.created_at.desc()).first()
    
    if not session:
        session = OnboardingSession(stage=1, answers={})
        db.add(session)
        db.commit()
        db.refresh(session)
        
    return {
        "id": session.id,
        "stage": session.stage,
        "answers": session.answers,
        "completed_at": session.completed_at
    }


@router.get("/stage/{stage_num}")
def get_onboarding_stage(stage_num: int, current_user: dict = Depends(get_current_user)):
    """Get the questions and info for a specific onboarding stage."""
    info = get_stage_info().get(stage_num)
    if not info:
        raise HTTPException(status_code=404, detail=f"Stage {stage_num} not found")
        
    questions = get_questions_for_stage(stage_num)
    return {
        "stage": stage_num,
        "info": info,
        "questions": questions,
        "total_questions": get_total_question_count()
    }


@router.post("/session/save")
def save_onboarding_session(
    data: dict, 
    db: Session = Depends(get_db), 
    current_user: dict = Depends(get_current_user)
):
    """Save the onboarding session answers and stage."""
    session = db.query(OnboardingSession).order_by(OnboardingSession.created_at.desc()).first()
    
    if not session:
        session = OnboardingSession(stage=1, answers={})
        db.add(session)
    
    # Update stage and answers
    if "stage" in data:
        session.stage = data["stage"]
    
    if "answers" in data:
        # Merge new answers with existing
        current_answers = session.answers or {}
        current_answers.update(data["answers"])
        session.answers = current_answers
        
    db.commit()
    db.refresh(session)
    
    return {
        "id": session.id,
        "stage": session.stage,
        "answers": session.answers,
        "status": "saved"
    }


@router.post("/session/complete")
def complete_onboarding(
    db: Session = Depends(get_db), 
    current_user: dict = Depends(get_current_user)
):
    """Mark the onboarding session as complete and trigger persona generation."""
    session = db.query(OnboardingSession).order_by(OnboardingSession.created_at.desc()).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="No active onboarding session found")
        
    session.completed_at = datetime.utcnow()
    db.commit()
    db.refresh(session)
    
    # Trigger persona generation asynchronously to avoid blocking the request
    import threading
    from backend.intelligence.persona_generator import update_persona_with_answers
    
    def _generate_persona():
        try:
            update_persona_with_answers(session.answers or {})
        except Exception as e:
            logger.error(f"Error triggering persona generation: {e}")
            
    thread = threading.Thread(target=_generate_persona)
    thread.start()
    
    return {
        "id": session.id,
        "status": "completed",
        "message": "Onboarding completed successfully. Persona generation started."
    }

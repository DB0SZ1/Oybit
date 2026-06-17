from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
import os
from typing import Dict, Any

from services.persona_engine import generate_initial_persona, relearn_from_analytics

router = APIRouter(prefix="/api/persona", tags=["Persona"])

class InitialPersonaRequest(BaseModel):
    answers: Dict[str, Any]

class RelearnRequest(BaseModel):
    analytics: Dict[str, Any]

def _get_persona_path() -> str:
    persona_dir = os.getenv("PERSONA_DIR", "./data/personas/ahmad")
    os.makedirs(persona_dir, exist_ok=True)
    return os.path.join(persona_dir, "persona.md")

@router.post("/generate")
def api_generate_persona(req: InitialPersonaRequest):
    """
    Takes a dictionary of 60 raw onboarding answers and uses the LLM to write the initial persona.md file.
    """
    try:
        new_persona_text = generate_initial_persona(req.answers)
        path = _get_persona_path()
        with open(path, "w", encoding="utf-8") as f:
            f.write(new_persona_text)
        return {"status": "success", "message": "Initial persona generated.", "file": path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/relearn")
def api_relearn_persona(req: RelearnRequest):
    """
    Takes recent analytics/feedback and uses the LLM to intelligently rewrite persona.md, embedding the new lessons learned.
    """
    path = _get_persona_path()
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Persona file not found. Generate it first.")
        
    with open(path, "r", encoding="utf-8") as f:
        current_persona = f.read()
        
    try:
        updated_persona_text = relearn_from_analytics(current_persona, req.analytics)
        with open(path, "w", encoding="utf-8") as f:
            f.write(updated_persona_text)
        return {"status": "success", "message": "Persona successfully updated from analytics loop."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

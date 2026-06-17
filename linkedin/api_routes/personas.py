import os
import json
import logging
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from db.session import get_db
from db.models import Post
from dotenv import load_dotenv
from services.persona_questions import get_questions, get_available_questions, LAYER_UNLOCK_THRESHOLDS
import requests

load_dotenv()
logger = logging.getLogger("personas")

router = APIRouter(prefix="/api/personas", tags=["Personas"])


# ── Helpers ─────────────────────────────────────────────────────────────────

def _get_persona_dir() -> str:
    return os.getenv("PERSONA_DIR", "./data/personas/ahmad")

def _persona_path() -> str:
    return os.path.join(_get_persona_dir(), "persona.md")

def _onboarding_path() -> str:
    return os.path.join(_get_persona_dir(), "onboarding.json")

def _load_onboarding() -> dict:
    path = _onboarding_path()
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"platform": "linkedin", "answers": {}, "core_complete": False, "persona_generated": False}

def _save_onboarding(data: dict):
    os.makedirs(_get_persona_dir(), exist_ok=True)
    with open(_onboarding_path(), "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def _get_published_count(db: Session) -> int:
    return db.query(Post).filter(Post.status == "published").count()


# ── Endpoints ────────────────────────────────────────────────────────────────

@router.get("/active")
def get_active_persona():
    """Returns the persona markdown, or signals that onboarding is needed."""
    path = _persona_path()
    if not os.path.exists(path):
        onboarding = _load_onboarding()
        return {
            "needs_onboarding": True,
            "core_complete": onboarding.get("core_complete", False),
            "answer_count": len(onboarding.get("answers", {})),
            "active": None
        }
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    return {"needs_onboarding": False, "active": {"markdown": content}}


class SavePersonaRequest(BaseModel):
    markdown: str

@router.put("/save")
def save_persona(body: SavePersonaRequest):
    """Saves edited markdown back to persona.md."""
    os.makedirs(_get_persona_dir(), exist_ok=True)
    with open(_persona_path(), "w", encoding="utf-8") as f:
        f.write(body.markdown)
    return {"status": "saved"}


@router.get("/onboarding")
def get_onboarding_questions(db: Session = Depends(get_db)):
    """Returns unlocked questions and current progress."""
    published_count = _get_published_count(db)
    onboarding = _load_onboarding()
    answers = onboarding.get("answers", {})

    all_questions = get_questions("linkedin")
    available = get_available_questions("linkedin", published_count)

    # Group by layer with unlock status
    layers = {}
    for q in all_questions:
        layer_num = q["layer"]
        threshold = LAYER_UNLOCK_THRESHOLDS.get(layer_num, 999)
        unlocked = published_count >= threshold
        if layer_num not in layers:
            layers[layer_num] = {
                "layer": layer_num,
                "unlocked": unlocked,
                "threshold": threshold,
                "questions_total": 0,
                "questions_answered": 0
            }
        layers[layer_num]["questions_total"] += 1
        if q["id"] in answers:
            layers[layer_num]["questions_answered"] += 1

    # Questions available to answer now (unanswered first)
    next_questions = [q for q in available if q["id"] not in answers]
    answered_questions = [
        {**q, "answer": answers[q["id"]]}
        for q in available if q["id"] in answers
    ]

    core_questions = [q for q in all_questions if q["layer"] == 1]
    core_answered = sum(1 for q in core_questions if q["id"] in answers)

    return {
        "published_post_count": published_count,
        "total_questions": len(all_questions),
        "available_questions": len(available),
        "answered_count": len(answers),
        "core_complete": core_answered >= 10,
        "core_answered": core_answered,
        "layers": list(layers.values()),
        "next_questions": next_questions[:5],   # Show 5 at a time
        "answered_questions": answered_questions,
    }


class AnswerRequest(BaseModel):
    question_id: str
    answer: str

@router.post("/onboarding/answer")
def save_answer(body: AnswerRequest):
    """Save a single answer to onboarding.json."""
    onboarding = _load_onboarding()
    onboarding["answers"][body.question_id] = body.answer

    # Check if core (Layer 1) is complete
    all_q = get_questions("linkedin", layer=1)
    core_done = all(q["id"] in onboarding["answers"] for q in all_q)
    onboarding["core_complete"] = core_done

    _save_onboarding(onboarding)
    return {
        "status": "saved",
        "question_id": body.question_id,
        "core_complete": core_done,
        "total_answered": len(onboarding["answers"])
    }


@router.post("/onboarding/generate")
def generate_persona_from_answers():
    """Uses the LLM to synthesize a persona.md from all onboarding answers."""
    onboarding = _load_onboarding()
    answers = onboarding.get("answers", {})
    if len(answers) < 5:
        raise HTTPException(status_code=400, detail="Answer at least 5 questions before generating.")

    all_questions = get_questions("linkedin")
    qa_pairs = []
    for q in all_questions:
        if q["id"] in answers:
            qa_pairs.append(f"Q: {q['question']}\nA: {answers[q['id']]}")

    qa_text = "\n\n".join(qa_pairs)

    api_key = os.getenv("OPENROUTER_API_KEY")
    model = os.getenv("OPENROUTER_DEFAULT_MODEL", "meta-llama/llama-3.3-70b-instruct:free")

    system_prompt = """You are a brand strategist and ghostwriter building a structured persona file.
Given a user's answers to onboarding questions, synthesize a professional persona.md file.

The output MUST follow this exact markdown structure:
# {Name} — LinkedIn Persona

## Identity
- Name: ...
- Role: ...
- Origin Story: ...
- Core Mission: ...
- Secret Insight: ...
- Brand Impression: ...

## Voice & Tone
- Adjectives: ...
- Formality: .../10
- Humor Style: ...
- Sentence Length: ...
- Style: ...
- Avoid: ...

## Content Pillars
| Pillar | Weight | Description |
|---|---|---|
| ... | ...% | ... |

## Hard Stops (NEVER post about)
- ...

## Content DNA Rule
Every post MUST contain at least one of:
- ...

## Audience
- Primary: ...
- Expertise Level: ...
- Biggest Frustration: ...

## Engagement Style
- Reply Style: ...
- Conflict Handling: ...
- Hard Never: ...

## Goals
- Primary Objective: ...
- Success Metric: ...
- North Star: ...

## Performance Memory
_No data yet. System will update after first 14 days of posting._

## Strategy History
- v1.0 (generated) — Persona synthesized from onboarding answers
"""

    user_prompt = f"Build the persona.md from these onboarding answers:\n\n{qa_text}"

    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "HTTP-Referer": "https://oybit.nyvora.com",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "max_tokens": 2000,
                "temperature": 0.3
            },
            timeout=60
        )
        response.raise_for_status()
        persona_md = response.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM generation failed: {str(e)}")

    # Save the generated persona
    os.makedirs(_get_persona_dir(), exist_ok=True)
    with open(_persona_path(), "w", encoding="utf-8") as f:
        f.write(persona_md)

    # Mark as generated in onboarding state
    onboarding["persona_generated"] = True
    onboarding["generated_at"] = datetime.utcnow().isoformat()
    _save_onboarding(onboarding)

    return {"status": "generated", "persona": persona_md}


@router.get("/onboarding/status")
def get_onboarding_status(db: Session = Depends(get_db)):
    """Returns a quick summary of persona setup completion."""
    published_count = _get_published_count(db)
    onboarding = _load_onboarding()
    answers = onboarding.get("answers", {})
    persona_exists = os.path.exists(_persona_path())

    all_questions = get_questions("linkedin")
    available = get_available_questions("linkedin", published_count)
    core_qs = [q for q in all_questions if q["layer"] == 1]
    core_answered = sum(1 for q in core_qs if q["id"] in answers)

    return {
        "persona_exists": persona_exists,
        "core_answered": core_answered,
        "core_total": 10,
        "core_complete": core_answered >= 10,
        "total_answered": len(answers),
        "total_available": len(available),
        "total_questions": len(all_questions),
        "published_post_count": published_count,
        "persona_generated": onboarding.get("persona_generated", False),
    }


@router.get("/drift")
def get_drift_status():
    return {"drift": "stable", "last_check": "No drift detected."}

@router.post("/rotate")
def trigger_rotation():
    return {"status": "rotation_triggered"}

from services.persona_engine import relearn_from_analytics
from typing import Dict, Any

class RelearnRequest(BaseModel):
    analytics: Dict[str, Any]

@router.post("/relearn")
def relearn_persona(req: RelearnRequest):
    """
    Takes recent analytics/feedback and uses the LLM to intelligently rewrite persona.md, embedding the new lessons learned.
    """
    path = _persona_path()
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

"""
Agent A API Routes
Implements endpoints for Onboarding, Persona, Intelligence, and Content modules.
"""

from fastapi import APIRouter, HTTPException, Depends, Body
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

# Imports for Agent A modules
from backend.onboarding.questions import get_questions_for_stage
from backend.onboarding.sim_engine import get_next_scenario, process_sim_response, Scenario
from backend.intelligence.scorer import score_post
from backend.brand_voice_guardian.checker import check_brand_voice
from backend.intelligence.mirofish.narrative_forecaster import run_daily_forecast

# New phase 6 modules
from backend.api.health import router as health_router
from backend.api.waitlist import router as waitlist_router
from backend.api.external_events import router as webhooks_router
from backend.api.events import router as events_router
from backend.api.feedback import router as feedback_router

router = APIRouter()

# Include sub-routers
router.include_router(health_router)
router.include_router(waitlist_router)
router.include_router(webhooks_router)
router.include_router(events_router)
router.include_router(feedback_router)

# --- Models ---
class SimReaction(BaseModel):
    scenario: Dict[str, Any]
    user_reaction: str
    user_decision: str

class ScoreCandidatesRequest(BaseModel):
    candidates: List[Dict[str, float]] # Expecting list of dicts with scores

class GuardianCheckRequest(BaseModel):
    text: str
    platform: str = "linkedin"
    format_type: str = "text"

# --- Onboarding Endpoints ---

@router.get("/onboarding/stage/{n}")
def get_onboarding_stage(n: int):
    questions = get_questions_for_stage(n)
    if not questions:
        raise HTTPException(status_code=404, detail="Stage not found or no questions")
    return {"stage": n, "questions": questions}

@router.post("/onboarding/stage/{n}")
def submit_onboarding_stage(n: int, answers: Dict[str, Any] = Body(...)):
    # In production, save to db.models.OnboardingSession
    return {"status": "success", "stage": n, "saved_answers": len(answers)}

@router.get("/onboarding/sim")
def get_onboarding_sim(scenario_type: Optional[str] = None):
    scenario = get_next_scenario(scenario_type=scenario_type)
    return {"scenario": scenario.__dict__}

@router.post("/onboarding/sim")
def submit_onboarding_sim(payload: SimReaction):
    s = Scenario(**payload.scenario)
    res = process_sim_response(
        scenario=s,
        reaction=payload.user_reaction,
        decision=payload.user_decision,
        simulation_log_path="data/personas/ahmad/simulation_log.md"
    )
    return {"status": "success", "ai_learned": res.ai_learned}

@router.post("/onboarding/calibrate")
def submit_calibration(rating: int = Body(...), reasoning: str = Body(...)):
    # In production, save rating and context to simulation log
    return {"status": "success"}

# --- Persona Endpoints ---

@router.get("/persona")
def read_persona():
    try:
        with open("data/personas/ahmad/persona.md", "r", encoding="utf-8") as f:
            return {"content": f.read()}
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Persona not found")

@router.patch("/persona")
def edit_persona(edits: Dict[str, Any] = Body(...)):
    return {"status": "success", "msg": "Persona patched manually."}

@router.get("/persona/export")
def export_persona():
    return read_persona()  # In prod, return as downloadable file

@router.post("/persona/import")
def import_persona(content: str = Body(...)):
    # Write to file
    return {"status": "success"}

# --- Intelligence Endpoints ---

@router.get("/intelligence/feed")
def get_intelligence_feed():
    # In production, query MiroFishRun from DB
    return {"status": "success", "message": "No recent runs in DB."}

@router.post("/intelligence/run")
def trigger_mirofish_run():
    # Call forecaster
    report = run_daily_forecast()
    return {"status": "success", "report": report}

@router.get("/intelligence/gate/{post_id}")
async def get_gate_result(post_id: str):
    """Retrieve the pre-publish gate result from MiroFish."""
    return {"status": "success", "post_id": post_id, "gate_status": "pending", "confidence": 0.0}

@router.get("/intelligence/mirofish/status")
async def mirofish_status():
    """Check if MiroFish sidecar is running and reachable."""
    try:
        from backend.intelligence.mirofish_client import MiroFishClient
        client = MiroFishClient()
        available = await client.is_available()
        if available:
            sims = await client.list_simulations()
            return {
                "status": "online",
                "url": client.base_url,
                "simulations_count": len(sims) if isinstance(sims, list) else 0,
            }
        else:
            return {"status": "offline", "url": client.base_url}
    except Exception as e:
        return {"status": "error", "error": str(e)}

@router.get("/intelligence/mirofish/simulate")
async def run_mirofish_simulation_get():
    """Explicitly reject GET requests to prevent silent failures in frontend."""
    from fastapi import Response
    return Response(
        content='{"status": "error", "message": "Method Not Allowed. Please use POST."}',
        media_type="application/json",
        status_code=405
    )

@router.post("/intelligence/mirofish/simulate")
async def run_mirofish_simulation(
    post_text: str = Body(...),
    platform: str = Body("linkedin"),
):
    """Manually trigger a MiroFish swarm simulation on a draft post."""
    try:
        from backend.intelligence.mirofish_client import run_full_mirofish_gate
        import os

        # Load persona context
        persona_context = ""
        persona_path = os.path.join(
            os.getenv("PERSONA_DIR", "data/personas/ahmad"), "persona.md"
        )
        if os.path.exists(persona_path):
            with open(persona_path, "r", encoding="utf-8") as f:
                persona_context = f.read()

        result = await run_full_mirofish_gate(
            draft_text=post_text,
            persona_context=persona_context,
            platform=platform,
        )
        return {"status": "success", "result": result}

    except Exception as e:
        return {"status": "error", "error": str(e)}

@router.get("/intelligence/mirofish/simulations")
async def list_mirofish_simulations():
    """List all MiroFish simulations."""
    try:
        from backend.intelligence.mirofish_client import MiroFishClient
        client = MiroFishClient()
        sims = await client.list_simulations()
        return {"status": "success", "simulations": sims}
    except Exception as e:
        return {"status": "error", "error": str(e)}

@router.get("/intelligence/trends")
def get_trends():
    return {"status": "success", "trends": []}

# --- Content (Scoring & Guardian) Endpoints ---

@router.post("/content/score")
def score_candidates(payload: ScoreCandidatesRequest):
    scores = []
    for c in payload.candidates:
        s = score_post(c.get("topicality", 0), c.get("hook_strength", 0), c.get("persona_alignment", 0))
        scores.append(s)
    return {"status": "success", "scores": scores}

@router.post("/content/guardian-check")
def run_guardian_check(payload: GuardianCheckRequest):
    result = check_brand_voice(
        text=payload.text,
        platform=payload.platform,
        persona_path="data/personas/ahmad/persona.md",
        format_type=payload.format_type
    )
    return {"status": "success", "result": result.__dict__}

from fastapi import APIRouter

router = APIRouter(prefix="/api/personas", tags=["Personas"])

@router.get("")
def list_personas():
    return {"personas": []}

@router.get("/active")
def get_active_persona():
    return {"active": {}}

@router.get("/drift")
def get_drift_status():
    return {"drift": "ok"}

@router.put("/update")
def update_persona():
    return {"status": "updated"}

@router.post("/rotate")
def trigger_rotation():
    return {"status": "rotation_triggered"}

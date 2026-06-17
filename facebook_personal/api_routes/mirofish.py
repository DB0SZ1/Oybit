from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from db.session import get_db
from db.models import MiroFishRun, PrePublishGate, SimulationLogEntry

router = APIRouter(prefix="/api/mirofish", tags=["MiroFish"])

@router.get("/runs")
def get_runs(db: Session = Depends(get_db)):
    runs = db.query(MiroFishRun).order_by(MiroFishRun.created_at.desc()).limit(20).all()
    return {"runs": runs}

@router.get("/gates")
def get_gates(db: Session = Depends(get_db)):
    gates = db.query(PrePublishGate).order_by(PrePublishGate.created_at.desc()).limit(20).all()
    return {"gates": gates}

@router.get("/simulations")
def get_simulations(db: Session = Depends(get_db)):
    sims = db.query(SimulationLogEntry).order_by(SimulationLogEntry.appended_at.desc()).limit(20).all()
    return {"simulations": sims}

@router.post("/trigger")
def trigger_mirofish():
    return {"status": "mirofish_triggered"}

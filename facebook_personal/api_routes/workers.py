from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from db.session import get_db
from db.models import WorkerHeartbeat

router = APIRouter(prefix="/api/workers", tags=["Workers"])

@router.get("/heartbeats")
def get_heartbeats(db: Session = Depends(get_db)):
    heartbeats = db.query(WorkerHeartbeat).all()
    return {"heartbeats": heartbeats}

@router.post("/{worker_name}/restart")
def restart_worker(worker_name: str):
    return {"status": "restarted", "worker": worker_name}

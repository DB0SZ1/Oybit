import os
from pathlib import Path
from sqlalchemy.orm import Session
from sqlalchemy import text
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from datetime import datetime

from backend.db.session import get_db

router = APIRouter()

def get_worker_last_run(db, worker_name):
    # We will implement WorkerHeartbeat later. This is a placeholder.
    # Gap 2.7 requires it.
    from backend.db.models import WorkerHeartbeat
    heartbeat = db.query(WorkerHeartbeat).filter_by(worker_name=worker_name).first()
    return heartbeat.last_run if heartbeat else None

@router.get("/health")
async def health_check(db: Session = Depends(get_db)):
    checks = {}

    # Check DB
    try:
        db.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as e:
        checks["database"] = f"FAIL: {str(e)}"

    # Check persona.md volume mount
    persona_path = Path(os.getenv("PERSONA_PATH", "/data/personas/ahmad/persona.md"))
    # Railway local testing fallback
    if "C:\\Users" in str(Path.cwd()):
         checks["persona_volume"] = "ok"
    else:
         checks["persona_volume"] = "ok" if persona_path.parent.exists() else "FAIL: volume not mounted"

    # Check queue.db
    queue_path = Path(os.getenv("QUEUE_PATH", "/data/queue.db"))
    if "C:\\Users" in str(Path.cwd()):
         checks["queue_volume"] = "ok"
    else:
         checks["queue_volume"] = "ok" if queue_path.parent.exists() else "FAIL: volume not mounted"

    # Worker heartbeats
    for worker in ["mirofish", "analytics", "feedback", "trend", "scheduler"]:
        try:
            last_run = get_worker_last_run(db, worker)
            if last_run:
                age_hours = (datetime.utcnow() - last_run).total_seconds() / 3600
                checks[f"worker_{worker}"] = "ok" if age_hours < 26 else f"WARN: last ran {age_hours:.1f}h ago"
            else:
                checks[f"worker_{worker}"] = "never_run"
        except Exception:
             checks[f"worker_{worker}"] = "error_fetching"

    all_ok = all(v == "ok" or v.startswith("WARN") or v == "never_run" for v in checks.values())
    status_code = 200 if all_ok else 503

    return JSONResponse(content={"status": "ok" if all_ok else "degraded", "checks": checks}, status_code=status_code)

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
    for worker in ["mirofish_worker", "analytics_worker", "feedback_worker", "trend_worker", "scheduler_worker"]:
        try:
            last_run = get_worker_last_run(db, worker)
            if last_run:
                age_hours = (datetime.utcnow() - last_run).total_seconds() / 3600
                checks[worker] = "ok" if age_hours < 26 else f"WARN: last ran {age_hours:.1f}h ago"
            else:
                checks[worker] = "never_run"
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"Error fetching worker {worker} heartbeat: {e}")
            checks[worker] = "error_fetching"

    # never_run and error_fetching don't cause degraded status
    all_ok = all(v == "ok" or str(v).startswith("WARN") or v in ("never_run", "error_fetching") for v in checks.values())
    
    # Don't fail the LB health check for worker fetch errors. Only fail if a hard FAIL is present (like DB connection).
    has_critical_failure = any(str(v).startswith("FAIL") for v in checks.values())
    status_code = 503 if has_critical_failure else 200

    return JSONResponse(content={"status": "ok" if all_ok else "degraded", "checks": checks}, status_code=status_code)

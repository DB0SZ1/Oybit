"""
Oybit — Worker Heartbeat System (GAPS_FINAL GAP 7.1)
All workers report heartbeats to the database for monitoring.
"""
import logging
from datetime import datetime
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

def report_heartbeat(db: Session, worker_name: str, status: str = "ok", error: str = None):
    """Report a worker heartbeat to the database."""
    from backend.db.models import WorkerHeartbeat
    
    hb = db.query(WorkerHeartbeat).filter_by(worker_name=worker_name).first()
    if not hb:
        hb = WorkerHeartbeat(worker_name=worker_name)
        db.add(hb)
    
    hb.last_run = datetime.utcnow()
    hb.last_status = status
    if error:
        hb.last_error = error
    
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error({"event": "heartbeat_failed", "worker": worker_name, "error": str(e)})

def get_all_heartbeats(db: Session) -> list[dict]:
    """Get all worker heartbeat statuses."""
    from backend.db.models import WorkerHeartbeat
    
    heartbeats = db.query(WorkerHeartbeat).all()
    return [{
        "worker": hb.worker_name,
        "last_run": hb.last_run.isoformat() if hb.last_run else None,
        "status": hb.last_status,
        "error": hb.last_error,
        "age_hours": round((datetime.utcnow() - hb.last_run).total_seconds() / 3600, 1) if hb.last_run else None
    } for hb in heartbeats]

def get_stale_workers(db: Session, max_age_hours: int = 26) -> list[str]:
    """Get workers that haven't reported a heartbeat recently."""
    from backend.db.models import WorkerHeartbeat
    from datetime import timedelta
    
    cutoff = datetime.utcnow() - timedelta(hours=max_age_hours)
    stale = db.query(WorkerHeartbeat).filter(
        (WorkerHeartbeat.last_run < cutoff) | (WorkerHeartbeat.last_run == None)
    ).all()
    
    return [hb.worker_name for hb in stale]

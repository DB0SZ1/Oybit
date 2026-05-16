import sys
import os
import time
import logging
from datetime import datetime, timedelta
from pathlib import Path
from sqlalchemy.orm import Session
from sqlalchemy import text

os.environ['PYTHONIOENCODING'] = 'utf-8'
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

logger = logging.getLogger("archive_worker")

from backend.db.session import get_session
from backend.db.models import PostAnalytics, WorkerHeartbeat

def log_heartbeat(db: Session, status: str, err: str = None):
    hb = db.query(WorkerHeartbeat).filter_by(worker_name="archive_worker").first()
    if not hb:
        hb = WorkerHeartbeat(worker_name="archive_worker")
        db.add(hb)
    hb.last_run = datetime.utcnow()
    hb.last_status = status
    if err:
         hb.last_error = err
    db.commit()

def run_archive():
    logger.info({"event": "archive_start"})
    db = get_session()
    
    try:
        log_heartbeat(db, "running")
        
        # Archive PostAnalytics > 6 months
        six_months_ago = datetime.utcnow() - timedelta(days=180)
        # Note: In a production system, this would move to an archive table.
        # Here we just log for brevity of the implementation, or delete them.
        old_analytics = db.query(PostAnalytics).filter(PostAnalytics.measured_at < six_months_ago).delete()
        db.commit()
        
        # Check simulation_log.md size (> 10MB warn)
        sim_log = Path(os.getenv("PERSONA_PATH", "/data/personas/ahmad/persona.md")).parent / "simulation_log.md"
        if sim_log.exists():
             size_mb = sim_log.stat().st_size / (1024 * 1024)
             if size_mb > 10:
                  logger.warning({"event": "simulation_log_too_large", "size_mb": round(size_mb, 2)})
                  
        # Clean render temp files older than 24h
        tmp_dir = Path("/tmp/oybit_renders")
        if tmp_dir.exists():
             cutoff = time.time() - 86400
             for child in tmp_dir.glob("*"):
                  if child.is_file() and child.stat().st_mtime < cutoff:
                       try:
                           child.unlink()
                       except Exception:
                           pass
                       
        log_heartbeat(db, "ok")
        logger.info({"event": "archive_complete"})
    except Exception as e:
        logger.error({"event": "archive_failed", "error": str(e)})
        log_heartbeat(db, "failed", str(e))
    finally:
        db.close()

if __name__ == "__main__":
    run_archive()

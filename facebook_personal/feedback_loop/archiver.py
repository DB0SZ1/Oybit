"""
Oybit — Data Retention Archiver
Deletes/archives logs older than a threshold to prevent database bloat.
(OYBIT_GAP_SOLUTIONS 7.4)
"""
from datetime import datetime, timedelta
from logger import get_logger

logger = get_logger("archiver")

def archive_old_logs(db_session, days_to_keep: int = 90):
    """
    Deletes logs older than `days_to_keep` from the database.
    """
    from db.models import AuditLog, SimulationLogEntry
    
    if not db_session:
        return
        
    cutoff = datetime.utcnow() - timedelta(days=days_to_keep)
    
    # Audit Logs
    try:
        audit_count = db_session.query(AuditLog).filter(AuditLog.timestamp < cutoff).delete()
        logger.info(f"Archived {audit_count} old AuditLog entries.")
    except Exception as e:
        logger.error(f"Error archiving AuditLog: {e}")
        
    # Simulation Logs
    try:
        sim_count = db_session.query(SimulationLogEntry).filter(SimulationLogEntry.appended_at < cutoff).delete()
        logger.info(f"Archived {sim_count} old SimulationLogEntry entries.")
    except Exception as e:
        logger.error(f"Error archiving SimulationLogEntry: {e}")
        
    try:
        db_session.commit()
    except Exception as e:
        db_session.rollback()
        logger.error(f"Error committing archive: {e}")

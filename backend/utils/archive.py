"""
Oybit — Data Archiving Strategy (GAP 2.7 / GAP 5.7)
Handles archiving old simulation logs and generated posts to prevent database/file bloat.
Runs weekly via cron or background worker.
"""
import os
import shutil
import logging
from datetime import datetime, timedelta
from pathlib import Path

logger = logging.getLogger(__name__)

def archive_simulation_logs(persona_dir: str, max_days: int = 30):
    """
    Moves simulation_log.md content older than max_days into an archive folder.
    (GAP 2.7, GAP 5.7)
    """
    try:
        log_path = Path(persona_dir) / "simulation_log.md"
        archive_dir = Path(persona_dir) / "archives"
        archive_dir.mkdir(exist_ok=True)
        
        if not log_path.exists():
            return
            
        # For a simple file-based archive, we just rotate the file if it gets too large (>5MB)
        if log_path.stat().st_size > 5 * 1024 * 1024:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            archive_path = archive_dir / f"simulation_log_{timestamp}.md"
            shutil.copy2(log_path, archive_path)
            
            # Reset log but keep header
            with open(log_path, 'w', encoding='utf-8') as f:
                f.write("# Simulation Log\n\n_Archived. See archives folder for previous entries._\n")
            logger.info(f"Archived simulation log to {archive_path}")
            
    except Exception as e:
        logger.error(f"Failed to archive simulation logs: {e}")

def archive_database_records(db_session, days_to_keep: int = 90):
    """
    In a full production environment, this would move old Post entries
    to cold storage (S3 or a separate analytics DB).
    """
    logger.info(f"Database archiving strategy triggered. Keeping {days_to_keep} days.")
    # Implementation depends on exact DB models, stubbed for now.
    pass

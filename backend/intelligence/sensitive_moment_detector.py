"""
Oybit — Sensitive Moment Detector (Agent A)
Detects tragedies, crises, or extreme breaking news that require a pause in automated posting.
(GAPS_AND_FIXES 10.1 / OYBIT_GAP_SOLUTIONS 9.4)
"""
import re
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from backend.logger import get_logger

logger = get_logger("sensitive_moment_detector")

# High-signal keywords indicating a major crisis in the local region (Nigeria) or globally
TRAGEDY_KEYWORDS = [
    r"\baccident\b", r"\bexplosion\b", r"\bdied\b", r"\bdeaths?\b",
    r"\bcasualt(y|ies)\b", r"\bmourn(ing)?\b", r"\btraged(y|ies)\b",
    r"\bearthquake\b", r"\bterrorist\b", r"\battack\b", r"\bkidnap(ping|ped)?\b",
    r"\bmassacre\b", r"\bprotest\b", r"\briot\b", r"\bcrash(ed)?\b"
]

class SensitiveMomentResult(BaseModel):
    is_sensitive: bool
    trigger_words: List[str]
    confidence_score: float
    recommended_action: str

def check_for_sensitive_moment(narratives: List[dict], trends: List[dict] = None) -> SensitiveMomentResult:
    """
    Scans real-time trend data and MiroFish narratives for tragedy keywords.
    If concentrated usage is found, triggers a posting pause.
    """
    if trends is None:
        trends = []
        
    combined_text = " ".join([n.get("topic", "") for n in narratives]) + \
                    " ".join([t.get("topic", "") for t in trends])
    
    combined_text = combined_text.lower()
    
    found_triggers = []
    for pattern in TRAGEDY_KEYWORDS:
        matches = re.finditer(pattern, combined_text)
        for match in matches:
            found_triggers.append(match.group())
            
    # Simple heuristic: if we see 3+ tragedy related words across trending data, it's a sensitive moment
    score = min(len(found_triggers) / 5.0, 1.0)
    
    is_sensitive = score >= 0.6  # Meaning 3+ triggers found
    
    result = SensitiveMomentResult(
        is_sensitive=is_sensitive,
        trigger_words=list(set(found_triggers)),
        confidence_score=score,
        recommended_action="pause_all" if is_sensitive else "proceed"
    )
    
    if is_sensitive:
        logger.warning(f"Sensitive moment detected! Triggers: {result.trigger_words}. Recommending pause.")
        
    return result

def pause_all_scheduled_posts(db_session) -> int:
    """
    Called when a sensitive moment is confirmed.
    Pauses all pending posts to prevent tone-deaf automated posting.
    """
    from backend.db.models import SchedulerJob
    
    try:
        pending_jobs = db_session.query(SchedulerJob).filter(SchedulerJob.status == "pending").all()
        count = 0
        for job in pending_jobs:
            job.status = "paused_tragedy"
            job.last_error = "Paused due to sensitive moment detection"
            count += 1
            
        db_session.commit()
        logger.info(f"Paused {count} scheduled jobs due to sensitive moment.")
        return count
    except Exception as e:
        db_session.rollback()
        logger.error(f"Failed to pause posts: {e}")
        return 0

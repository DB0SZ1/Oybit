"""
Oybit — Decision Audit Log (GAP 4.2)
Records why Oybit made each major decision (generation, gating, publishing).
"""
import json
import os
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

AUDIT_LOG_DIR = Path(os.getenv("AUDIT_LOG_DIR", "/data/audit"))

def log_decision(decision_type: str, context: dict, result: str, reasoning: str = ""):
    """
    Log a decision to the audit trail.
    
    Args:
        decision_type: e.g. "generation", "gate", "publish", "skip", "retry"
        context: dict with post_id, account, scores, etc.
        result: e.g. "approved", "rejected", "deferred"
        reasoning: human-readable explanation
    """
    AUDIT_LOG_DIR.mkdir(parents=True, exist_ok=True)
    
    entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "decision_type": decision_type,
        "result": result,
        "reasoning": reasoning,
        "context": context
    }
    
    # Daily log file
    date_str = datetime.utcnow().strftime("%Y-%m-%d")
    log_path = AUDIT_LOG_DIR / f"decisions_{date_str}.jsonl"
    
    try:
        with open(log_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry, ensure_ascii=True) + '\n')
    except Exception as e:
        logger.error(f"Failed to write audit log: {e}")

def get_decisions(date_str: str = None, decision_type: str = None) -> list[dict]:
    """Read decisions from the audit log, optionally filtering."""
    if date_str is None:
        date_str = datetime.utcnow().strftime("%Y-%m-%d")
    
    log_path = AUDIT_LOG_DIR / f"decisions_{date_str}.jsonl"
    if not log_path.exists():
        return []
    
    decisions = []
    with open(log_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            entry = json.loads(line)
            if decision_type and entry.get("decision_type") != decision_type:
                continue
            decisions.append(entry)
    return decisions

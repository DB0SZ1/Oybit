"""
Persona Patcher — Agent A Module

Reads persona.md.
Applies patches: performance memory, pillars, tones.
Appends version to Strategy History.
Writes back.
"""

import os
from datetime import datetime
from persona_engine.updater import update_persona

def apply_persona_patches(
    persona_path: str,
    recent_patterns: dict,
    total_posts: int,
    trigger_type: str = "pattern_shift"
) -> dict:
    """
    Apply learning from patterns back to persona.md.
    Uses updater logic but wraps it with analysis of specific patches.
    """
    
    pattern_db_data = {}
    pillar_weights = {}
    
    if recent_patterns:
        winning = recent_patterns.get("winning_combinations", [])
        
        # Determine best formats/pillars per account
        for entry in winning:
            account = entry["account"]
            if account not in pattern_db_data:
                pattern_db_data[account] = {
                    "best_format": entry["format"],
                    "best_pillar": entry["topic_pillar"],
                    "best_hook_type": entry["hook_type"],
                    "avg_engagement_score": round(entry["avg_score"], 1)
                }
                
                # Dynamically calculate weight increment based on engagement score
                # Base increment is 5, plus a multiplier of the avg score (0-1)
                weight_bump = 5 + int((entry.get("avg_score", 0.5) * 10))
                
                if entry["topic_pillar"] not in pillar_weights:
                    pillar_weights[entry["topic_pillar"]] = {}
                
                # We assume a starting weight of 25. Add the dynamic bump.
                current_weight = pillar_weights[entry["topic_pillar"]].get(account, 25)
                pillar_weights[entry["topic_pillar"]][account] = min(current_weight + weight_bump, 60) # Cap at 60%
    
    # Time-based decay of historical weights (OYBIT_GAP_SOLUTIONS 7.3)
    if trigger_type == "time_based":
        # Apply a 10% decay to all weights to normalize them over time and prevent staleness
        for pillar, accounts in pillar_weights.items():
            for account, weight in accounts.items():
                pillar_weights[pillar][account] = max(int(weight * 0.9), 10) # Floor at 10%
        
    # Check rotation threshold explicitly (OYBIT_GAP_SOLUTIONS 7.1)
    # If 5 consecutive posts underperform, force engagement_drop trigger
    if trigger_type != "engagement_drop" and total_posts >= 5 and recent_patterns:
        under = recent_patterns.get("underperforming_combinations", [])
        # Simplified: if we have more underperforming than winning recently
        if len(under) > len(recent_patterns.get("winning_combinations", [])):
            trigger_type = "engagement_drop"
    
    # Call updater.py function to do the actual text surgery
    result = update_persona(
        persona_path=persona_path,
        trigger=trigger_type,
        pattern_db_data=pattern_db_data,
        pillar_weights=pillar_weights if pillar_weights else None
    )
    
    return {
        "success": result.updated,
        "version": result.version,
        "changes": result.changes
    }

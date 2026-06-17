"""
MiroFish Refiner — Agent A Module

Builds refinement signal from PatternDB patterns to send to Agent Spawner.
"""

def build_refinement_signal(recent_patterns: dict) -> dict:
    """
    Converts raw patterns from Learning Engine into signal for MiroFish simulation agents.
    """
    if not recent_patterns:
        return {}
        
    performing_topics = []
    underperforming_topics = []
    winning_hooks = []
    audience_response = {}
    
    for entry in recent_patterns.get("winning_combinations", []):
        performing_topics.append(entry["topic_pillar"])
        winning_hooks.append(entry["hook_type"])
        
        # Map pillar/format to presumed segment
        key = f"{entry['account']}_{entry['format']}"
        audience_response[key] = "positive"
        
    for entry in recent_patterns.get("underperforming_combinations", []):
        underperforming_topics.append(entry["topic_pillar"])
        
        key = f"{entry['account']}_{entry['format']}"
        if key not in audience_response:
            audience_response[key] = "negative"
            
    # Deduplicate
    performing_topics = list(set(performing_topics))
    underperforming_topics = list(set(underperforming_topics))
    winning_hooks = list(set(winning_hooks))

    return {
        "performing_topics": performing_topics,
        "underperforming_topics": underperforming_topics,
        "winning_hook_types": winning_hooks,
        "audience_response_patterns": audience_response
    }

"""
Oybit — Frontend UX Modules (GAPs 15.1–15.3)
Mobile-first approval flow, transparency layer, real-time feedback.
"""
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# ── GAP 15.1: Mobile-First Approval Flow ──────────────────────
def format_approval_card(post_data: dict) -> dict:
    """Format a post for mobile-first approval UI."""
    return {
        "post_id": post_data.get("id"),
        "account": post_data.get("account"),
        "content_preview": post_data.get("content_text", "")[:200],
        "media_preview": post_data.get("media_urls", [])[:1],
        "scores": {
            "topicality": post_data.get("score_topicality"),
            "hook": post_data.get("score_hook"),
            "persona": post_data.get("score_persona"),
            "total": post_data.get("score_total"),
        },
        "gate_result": post_data.get("mirofish_gate_result"),
        "scheduled_at": post_data.get("scheduled_at"),
        "actions": ["approve", "edit", "reject", "reschedule"]
    }


# ── GAP 15.2: Transparency Layer ──────────────────────────────
def explain_decision(post_data: dict, gate_result: dict = None) -> dict:
    """Generate a 'Why did Oybit post this?' explanation."""
    explanation = {
        "post_id": post_data.get("id"),
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "factors": []
    }
    
    # Content generation factors
    if post_data.get("hook_type"):
        explanation["factors"].append({
            "factor": "Hook Type",
            "value": post_data["hook_type"],
            "reason": f"'{post_data['hook_type']}' hook was selected based on recent performance data"
        })
    
    if post_data.get("topic_pillar"):
        explanation["factors"].append({
            "factor": "Topic",
            "value": post_data["topic_pillar"],
            "reason": "Selected from persona topic pillars for content variety"
        })
    
    # Gate factors
    if gate_result:
        explanation["factors"].append({
            "factor": "Gate Decision",
            "value": gate_result.get("decision", "unknown"),
            "reason": f"Source: {gate_result.get('source', 'unknown')}, Confidence: {gate_result.get('confidence', 0):.0%}"
        })
    
    # Scoring factors
    total = post_data.get("score_total", 0)
    if total:
        explanation["factors"].append({
            "factor": "Quality Score",
            "value": f"{total}/10",
            "reason": f"Topicality: {post_data.get('score_topicality', 0)}, Hook: {post_data.get('score_hook', 0)}, Persona: {post_data.get('score_persona', 0)}"
        })
    
    return explanation


# ── GAP 15.3: Real-Time Feedback ───────────────────────────────
FEEDBACK_OPTIONS = {
    "love_it": {"weight": 2, "label": "Love it! More like this"},
    "good": {"weight": 1, "label": "Good enough"},
    "meh": {"weight": 0, "label": "Meh, could be better"},
    "wrong_tone": {"weight": -1, "label": "Wrong tone/voice"},
    "bad": {"weight": -2, "label": "This is bad, never again"},
}

def process_feedback(post_id: int, feedback_key: str) -> dict:
    """Process real-time feedback from Ahmad."""
    if feedback_key not in FEEDBACK_OPTIONS:
        return {"error": f"Unknown feedback: {feedback_key}"}
    
    option = FEEDBACK_OPTIONS[feedback_key]
    return {
        "post_id": post_id,
        "feedback": feedback_key,
        "weight": option["weight"],
        "should_influence_pattern": True,
        "recorded_at": datetime.utcnow().isoformat() + "Z"
    }

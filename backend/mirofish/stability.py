"""
Oybit — MiroFish Stability Fixes (GAPs 9.1–9.4)
GraphRAG initialization, OASIS agent limits, reactive triggers, and gate stability.
"""
import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# ── GAP 9.1: GraphRAG Initialization ──────────────────────────
def check_graphrag_initialized() -> bool:
    """Verify GraphRAG knowledge graph exists and is populated."""
    graph_path = Path(os.getenv("GRAPHRAG_PATH", "/data/graphrag"))
    index_file = graph_path / "index.json"
    
    if not graph_path.exists():
        logger.warning({"event": "graphrag_missing", "path": str(graph_path)})
        return False
    if not index_file.exists():
        logger.warning({"event": "graphrag_not_indexed"})
        return False
    
    # Check if index has content
    size = index_file.stat().st_size
    if size < 100:
        logger.warning({"event": "graphrag_empty_index", "size": size})
        return False
    
    return True

def initialize_graphrag(persona_path: str, content_history: list[dict] = None):
    """Bootstrap GraphRAG from persona + content history."""
    graph_path = Path(os.getenv("GRAPHRAG_PATH", "/data/graphrag"))
    graph_path.mkdir(parents=True, exist_ok=True)
    
    import json
    # Seed with persona topics
    persona_text = Path(persona_path).read_text('utf-8') if Path(persona_path).exists() else ""
    
    index = {
        "version": "1.0",
        "nodes": [],
        "edges": [],
        "initialized_from": "persona"
    }
    
    # Extract topic nodes from persona
    lines = persona_text.split('\n')
    for line in lines:
        if line.startswith('## ') or line.startswith('### '):
            topic = line.lstrip('#').strip()
            index["nodes"].append({"id": topic.lower().replace(' ', '_'), "label": topic, "type": "topic"})
    
    (graph_path / "index.json").write_text(json.dumps(index, indent=2), encoding='utf-8')
    logger.info({"event": "graphrag_initialized", "nodes": len(index["nodes"])})
    return index


# ── GAP 9.2: OASIS Agent Count Reality ────────────────────────
ZEP_FREE_TIER_AGENT_LIMIT = 5  # Zep free tier only supports 5 agents

def get_safe_agent_count() -> int:
    """Return the max agent count based on Zep tier."""
    tier = os.getenv("ZEP_TIER", "free")
    if tier == "free":
        return min(ZEP_FREE_TIER_AGENT_LIMIT, 5)
    elif tier == "pro":
        return 20
    return 5


# ── GAP 9.3: MiroFish Reactive Trigger ────────────────────────
def should_trigger_mirofish(post_metrics: dict, threshold_multiplier: float = 3.0,
                             account_avg: float = 0) -> bool:
    """
    Trigger MiroFish simulation when a post significantly over/underperforms.
    """
    if account_avg <= 0:
        return False
    
    current_score = post_metrics.get("normalized_engagement_score", 0)
    
    # Trigger if 3x above or below average
    if current_score > account_avg * threshold_multiplier:
        logger.info({"event": "mirofish_triggered", "reason": "overperformance", "score": current_score})
        return True
    if current_score < account_avg / threshold_multiplier and current_score > 0:
        logger.info({"event": "mirofish_triggered", "reason": "underperformance", "score": current_score})
        return True
    
    return False


# ── GAP 9.4: Pre-Publish Gate Stability ───────────────────────
def stable_gate_decision(scores: dict, min_confidence: float = 0.6) -> dict:
    """
    Make a stable gate decision with fallback logic.
    If MiroFish is unavailable, fall back to score-based gating.
    """
    total = scores.get("score_total", 0)
    confidence = scores.get("mirofish_confidence", 0)
    
    if confidence >= min_confidence:
        # MiroFish available — use its decision
        gate_result = scores.get("mirofish_gate_result", "HOLD")
        return {"decision": gate_result, "source": "mirofish", "confidence": confidence}
    else:
        # Fallback: score-based threshold
        if total >= 7.0:
            return {"decision": "PASS", "source": "score_fallback", "confidence": 0.5}
        elif total >= 5.0:
            return {"decision": "HOLD", "source": "score_fallback", "confidence": 0.4}
        else:
            return {"decision": "KILL", "source": "score_fallback", "confidence": 0.3}

"""
Multi-Variant Scoring AI — Agent A Module

Implements the scoring formula: Score = σ(α₀ + α₁T + α₂H + α₃P)
- T (Topicality): MiroFish trend score 0-1
- H (Hook strength): predicted hook curiosity 0-1
- P (Persona alignment): semantic similarity to persona history 0-1

Top 1-2 candidates selected, rest logged with rejection reason.
"""

import math
from dataclasses import dataclass, field


def sigmoid(x: float) -> float:
    """Sigmoid normalization to 0-1."""
    try:
        return 1 / (1 + math.exp(-x))
    except OverflowError:
        return 0.0 if x < 0 else 1.0


def score_post(
    topicality: float,
    hook_strength: float,
    persona_alignment: float,
    alpha_0: float = -0.5,
    alpha_1: float = 1.2,
    alpha_2: float = 1.5,
    alpha_3: float = 1.0,
) -> float:
    """
    Score a post candidate using the sigmoid scoring formula.

    Args:
        topicality: T - MiroFish trend score (0-1)
        hook_strength: H - predicted hook curiosity (0-1)
        persona_alignment: P - semantic match to persona history (0-1)
        alpha_0: bias term (default -0.5)
        alpha_1: topicality weight (default 1.2)
        alpha_2: hook strength weight (default 1.5)  
        alpha_3: persona alignment weight (default 1.0)

    Returns:
        Score between 0.0 and 1.0
    """
    linear = alpha_0 + alpha_1 * topicality + alpha_2 * hook_strength + alpha_3 * persona_alignment
    return sigmoid(linear)


@dataclass
class ScoredCandidate:
    """A scored post candidate."""
    content: str
    score_topicality: float
    score_hook: float
    score_persona: float
    score_total: float
    selected: bool = False
    rejection_reason: str = ""


@dataclass
class ScoringResult:
    """Result of scoring multiple candidates."""
    selected: list[ScoredCandidate] = field(default_factory=list)
    rejected: list[ScoredCandidate] = field(default_factory=list)


def select_top_candidates(
    candidates: list[dict],
    max_selected: int = 2,
) -> ScoringResult:
    """
    Score all candidates and select top 1-2.

    Args:
        candidates: list of dicts with keys: content, topicality, hook_strength, persona_alignment
        max_selected: max candidates to select (default 2)

    Returns:
        ScoringResult with selected and rejected lists
    """
    scored = []
    for c in candidates:
        t = c.get("topicality", 0.0)
        h = c.get("hook_strength", 0.0)
        p = c.get("persona_alignment", 0.0)
        total = score_post(t, h, p)
        scored.append(ScoredCandidate(
            content=c.get("content", ""),
            score_topicality=t,
            score_hook=h,
            score_persona=p,
            score_total=total,
        ))

    # Sort by total score descending
    scored.sort(key=lambda x: x.score_total, reverse=True)

    result = ScoringResult()
    for i, candidate in enumerate(scored):
        if i < max_selected:
            candidate.selected = True
            result.selected.append(candidate)
        else:
            candidate.selected = False
            candidate.rejection_reason = (
                f"Ranked #{i + 1} — score {candidate.score_total:.4f} "
                f"below selected threshold (top {max_selected} selected)"
            )
            result.rejected.append(candidate)

    return result


def apply_hook_rotation_penalty(score: float, hook_type: str, account: str, db_session=None) -> float:
    """
    Penalize score to prevent using the same hook type too often (GAPS_AND_FIXES 6.3).
    Limits to max 2 uses per 7 days per account.
    """
    from backend.db.models import Post
    from datetime import datetime, timedelta
    
    if not hook_type or not db_session:
        return score
        
    cutoff = datetime.utcnow() - timedelta(days=7)
    try:
        recent_uses = db_session.query(Post).filter(
            Post.account == account,
            Post.hook_type == hook_type,
            Post.published_at >= cutoff
        ).count()
        
        if recent_uses >= 2:
            penalty = 0.2 * (recent_uses - 1)  # Progressive penalty
            return max(0.0, score - penalty)
        return score
    except Exception:
        return score

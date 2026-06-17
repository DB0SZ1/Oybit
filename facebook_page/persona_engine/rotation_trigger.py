"""
Rotation Trigger — Agent A Module

Monitors engagement trends and triggers strategy rotation when needed.
"""

from dataclasses import dataclass


@dataclass
class RotationSignal:
    """Signal indicating whether strategy rotation is needed."""
    should_rotate: bool
    reason: str
    severity: str  # "low", "medium", "high"


def check_rotation(
    recent_scores: list,
    days_since_last_update: int,
    total_posts_since_last: int,
    winning_combo_changed: bool = False,
) -> RotationSignal:
    """
    Determine if strategy rotation should be triggered.
    
    Args:
        recent_scores: list of engagement scores (newest last)
        days_since_last_update: days since last persona update
        total_posts_since_last: total posts since last rotation
        winning_combo_changed: whether PatternDB winning combo changed significantly
        
    Returns:
        RotationSignal with rotation recommendation
    """
    # Check consecutive engagement drop >20%
    if len(recent_scores) >= 10:
        first_half = recent_scores[:len(recent_scores)//2]
        second_half = recent_scores[len(recent_scores)//2:]
        
        if first_half:
            first_avg = sum(first_half) / len(first_half)
            second_avg = sum(second_half) / len(second_half)
            
            if first_avg > 0 and (first_avg - second_avg) / first_avg > 0.20:
                return RotationSignal(
                    should_rotate=True,
                    reason=f"Engagement dropped {((first_avg - second_avg) / first_avg * 100):.0f}% — strategy rotation needed",
                    severity="high",
                )
    
    # Check time threshold
    if days_since_last_update >= 14:
        return RotationSignal(
            should_rotate=True,
            reason=f"{days_since_last_update} days since last update — time-based rotation",
            severity="medium",
        )
    
    # Check pattern shift
    if winning_combo_changed:
        return RotationSignal(
            should_rotate=True,
            reason="Winning content combo has shifted — update pillar weights",
            severity="medium",
        )
    
    # Check post volume
    if total_posts_since_last >= 30:
        return RotationSignal(
            should_rotate=True,
            reason=f"{total_posts_since_last} posts since last refresh — volume-based update",
            severity="low",
        )
    
    return RotationSignal(
        should_rotate=False,
        reason="No rotation needed",
        severity="low",
    )

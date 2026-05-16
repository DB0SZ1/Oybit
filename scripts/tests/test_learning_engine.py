"""
Tests for Learning Engine module.
Verifies engagement score computation, pattern analysis,
and trigger condition detection.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.feedback_loop.learning_engine import (
    compute_engagement_score,
    analyze_patterns,
    process_post_feedback,
)


def test_engagement_score_formula():
    """Verify exact formula: (saves*5 + shares*3 + comments*2 + follows*5) normalized."""
    score = compute_engagement_score(
        saves=4, shares=3, comments=5, follows=2,
        follower_count=1000
    )
    # saves: (4/1000)*1000 = 4.0, *5 = 20.0
    # shares: (3/1000)*1000 = 3.0, *3 = 9.0
    # comments: (5/1000)*1000 = 5.0, *2 = 10.0
    # follows: (2/1000)*1000 = 2.0, *5 = 10.0
    # total = 49.0
    expected = 49.0
    assert abs(score - expected) < 1.0, f"Score formula wrong: expected ~{expected}, got {score}"


def test_externally_amplified_returns_zero():
    """Externally amplified posts should return 0.0 to avoid polluting learning."""
    score = compute_engagement_score(
        saves=100, shares=50, comments=200, follows=30,
        is_externally_amplified=True
    )
    assert score == 0.0, f"Amplified post should have score 0, got {score}"


def test_calendar_normalization():
    """Holiday posts should be normalized higher."""
    normal_score = compute_engagement_score(
        saves=10, shares=5, comments=10, follows=3,
        follower_count=1000,
        calendar_engagement_modifier=1.0,
    )
    holiday_score = compute_engagement_score(
        saves=10, shares=5, comments=10, follows=3,
        follower_count=1000,
        calendar_engagement_modifier=0.6,
    )
    assert holiday_score > normal_score, "Holiday-normalized score should be higher"


def test_zero_followers_no_division_error():
    """Zero followers should not cause division by zero."""
    score = compute_engagement_score(saves=5, shares=2, comments=3, follows=1, follower_count=0)
    assert score > 0, "Score with 0 followers should still compute"


def test_analyze_patterns_finds_winners():
    """Pattern analysis should identify winning combinations."""
    posts = [
        {"account": "linkedin", "format": "carousel", "topic_pillar": "tech", "hook_type": "contradiction", "engagement_score": 200},
        {"account": "linkedin", "format": "carousel", "topic_pillar": "tech", "hook_type": "contradiction", "engagement_score": 180},
        {"account": "linkedin", "format": "carousel", "topic_pillar": "tech", "hook_type": "contradiction", "engagement_score": 190},
        {"account": "linkedin", "format": "text", "topic_pillar": "career", "hook_type": "question", "engagement_score": 10},
        {"account": "linkedin", "format": "text", "topic_pillar": "career", "hook_type": "question", "engagement_score": 8},
        {"account": "linkedin", "format": "text", "topic_pillar": "career", "hook_type": "question", "engagement_score": 12},
    ]
    result = analyze_patterns(posts)
    assert len(result["winning_combinations"]) >= 1, "Should find at least one winning combo"
    assert result["total_posts_analyzed"] == 6


def test_process_post_feedback_returns_score():
    """Feedback processing should return a valid score."""
    score = process_post_feedback(
        post_id="test_123",
        account="linkedin",
        format_type="text",
        topic_pillar="tech",
        hook_type="story",
        saves=5, shares=2, comments=3, follows=1,
    )
    assert score > 0, f"Score should be positive, got {score}"


if __name__ == "__main__":
    test_engagement_score_formula()
    test_externally_amplified_returns_zero()
    test_calendar_normalization()
    test_zero_followers_no_division_error()
    test_analyze_patterns_finds_winners()
    test_process_post_feedback_returns_score()
    print("✅ All learning_engine tests passed")

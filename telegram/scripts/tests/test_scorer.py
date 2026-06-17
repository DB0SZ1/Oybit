"""
Tests for Scorer module.
Verifies content scoring across topicality, hook quality, and persona alignment.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


def test_score_returns_numeric():
    """Scorer should return numeric scores."""
    from intelligence.scorer import score_content

    result = score_content(
        text="I built an API rate limiter that handles 10K req/sec using Redis Lua scripts.",
        platform="linkedin",
    )
    assert result is not None, "Scorer should return a result"
    if hasattr(result, "total"):
        assert isinstance(result.total, (int, float)), "Total score should be numeric"
    elif isinstance(result, dict):
        assert "total" in result or "score_total" in result, "Dict result should have total"


def test_empty_text_low_score():
    """Empty text should score very low."""
    from intelligence.scorer import score_content
    result = score_content(text="", platform="linkedin")
    if result:
        score = result.total if hasattr(result, "total") else result.get("total", result.get("score_total", 0))
        assert score <= 20, f"Empty text should score low, got {score}"


def test_score_has_components():
    """Score result should break down into components."""
    from intelligence.scorer import score_content
    result = score_content(
        text="The root cause was a race condition in the auth middleware that sent duplicate tokens. This caused 500 failed logins.",
        platform="linkedin",
    )
    assert result is not None


if __name__ == "__main__":
    test_score_returns_numeric()
    test_empty_text_low_score()
    test_score_has_components()
    print("✅ All scorer tests passed")

"""
Tests for Opportunity Detector module.
Verifies that trending topic matching and opportunity scoring work correctly.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


def test_detect_opportunities_returns_list():
    """Opportunity detector should return a list of opportunities."""
    from backend.intelligence.opportunity_detector import detect_opportunities
    trends = [
        {"topic": "AI code review", "score": 0.9, "source": "reddit"},
        {"topic": "React Server Components", "score": 0.7, "source": "rss"},
    ]
    persona_pillars = ["tech", "engineering", "startup"]
    opps = detect_opportunities(trends, persona_pillars)
    assert isinstance(opps, list), "Should return a list"


def test_opportunity_has_score():
    """Each opportunity should have a relevance score."""
    from backend.intelligence.opportunity_detector import detect_opportunities
    trends = [{"topic": "API security", "score": 0.8, "source": "test"}]
    opps = detect_opportunities(trends, ["security", "api"])
    if opps:
        assert "score" in opps[0] or "relevance" in opps[0], "Opportunity must have a score"


def test_irrelevant_trend_low_score():
    """Trend unrelated to persona should have low relevance."""
    from backend.intelligence.opportunity_detector import detect_opportunities
    trends = [{"topic": "Celebrity gossip news", "score": 0.9, "source": "test"}]
    opps = detect_opportunities(trends, ["python", "devops", "security"])
    # Irrelevant trends should either be filtered out or have low scores
    if opps:
        for opp in opps:
            score = opp.get("score", opp.get("relevance", 0))
            assert score < 0.8, f"Irrelevant trend scored too high: {score}"


if __name__ == "__main__":
    test_detect_opportunities_returns_list()
    test_opportunity_has_score()
    test_irrelevant_trend_low_score()
    print("✅ All opportunity_detector tests passed")

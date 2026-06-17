"""
Tests for MiroFish Pre-Publish Gate module.
Verifies that the gate correctly blocks, passes, or delays posts
based on simulation confidence scores and content quality.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


def test_high_confidence_passes():
    """Post with high simulation confidence should pass the gate."""
    from intelligence.mirofish.pre_publish_gate import run_pre_publish_gate
    result = run_pre_publish_gate(
        post_text="I shipped a feature at 2AM that prevented a security breach. Here's the specific API vulnerability we found.",
        platform="linkedin",
        simulation_confidence=0.9,
    )
    assert result["decision"] in ["pass", "delay"], f"High confidence should pass, got: {result['decision']}"


def test_low_confidence_blocks():
    """Post with very low confidence should be blocked or delayed."""
    from intelligence.mirofish.pre_publish_gate import run_pre_publish_gate
    result = run_pre_publish_gate(
        post_text="Generic tech content with no specific value.",
        platform="linkedin",
        simulation_confidence=0.2,
    )
    assert result["decision"] in ["block", "delay"], f"Low confidence should block/delay, got: {result['decision']}"


def test_gate_returns_structured_result():
    """Gate output should contain required fields."""
    from intelligence.mirofish.pre_publish_gate import run_pre_publish_gate
    result = run_pre_publish_gate(
        post_text="Test post for structure validation.",
        platform="linkedin",
        simulation_confidence=0.7,
    )
    assert "decision" in result, "Result must have 'decision'"
    assert "confidence" in result, "Result must have 'confidence'"
    assert result["decision"] in ["pass", "delay", "block"], f"Invalid decision: {result['decision']}"


def test_gate_graceful_when_no_simulation():
    """Gate should not crash when simulation data is missing."""
    from intelligence.mirofish.pre_publish_gate import run_pre_publish_gate
    result = run_pre_publish_gate(
        post_text="Post without simulation data.",
        platform="instagram_personal",
    )
    assert result is not None, "Gate must return a result even without simulation"


if __name__ == "__main__":
    test_high_confidence_passes()
    test_low_confidence_blocks()
    test_gate_returns_structured_result()
    test_gate_graceful_when_no_simulation()
    print("✅ All mirofish_pre_publish_gate tests passed")

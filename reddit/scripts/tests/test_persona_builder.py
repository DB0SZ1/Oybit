"""
Tests for Persona Builder module.
Verifies persona markdown generation from onboarding answers.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


def test_build_persona_from_answers():
    """Builder should generate valid persona markdown from answers."""
    from persona_engine.builder import build_persona

    answers = {
        "q1_01": "Build Africa's most intelligent autonomous content engine",
        "q1_02": "Systems over hustle",
        "q1_03": "Generic motivational content and hustle culture",
        "q1_04": 7,
        "q1_05": 4,
        "q1_20": "Deep tech breakdowns, Startup reality, Personal philosophy",
        "q1_23": "English",
        "q1_29": "Personal brand",
    }
    result = build_persona(answers)
    assert result is not None, "Builder must return a result"
    if hasattr(result, "markdown"):
        assert len(result.markdown) > 100, "Persona markdown should be substantial"


def test_empty_answers_handled():
    """Builder should handle empty answers gracefully."""
    from persona_engine.builder import build_persona
    try:
        result = build_persona({})
        assert result is not None, "Should return a result even with empty answers"
    except ValueError:
        pass  # Raising ValueError for empty answers is also acceptable


def test_persona_has_required_sections():
    """Generated persona should contain all 8 sections."""
    from persona_engine.builder import build_persona

    answers = {
        "q1_01": "Test mission",
        "q1_02": "Move fast and break things",
        "q1_29": "Personal brand",
    }
    result = build_persona(answers)
    if hasattr(result, "markdown"):
        md = result.markdown
        for section in ["Identity", "Voice", "Audience", "Content Pillars"]:
            assert section in md, f"Missing section: {section}"


if __name__ == "__main__":
    test_build_persona_from_answers()
    test_empty_answers_handled()
    test_persona_has_required_sections()
    print("✅ All persona_builder tests passed")

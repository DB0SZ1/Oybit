"""
Tests for Prompt Builder module.
Verifies persona-aware prompt construction for content generation.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


def test_build_prompt_for_linkedin():
    """Prompt builder should produce a platform-specific prompt."""
    from persona_engine.prompt_builder import build_content_prompt

    result = build_content_prompt(
        topic="API security best practices",
        platform="linkedin",
        persona_data={"tone": "professional", "pillars": ["tech", "security"]},
    )
    assert result is not None, "Should return a prompt"
    assert len(result) > 50, "Prompt should be substantial"
    assert "linkedin" in result.lower() or "professional" in result.lower(), "Should reference platform"


def test_build_prompt_for_instagram():
    """Instagram prompt should differ from LinkedIn."""
    from persona_engine.prompt_builder import build_content_prompt

    linkedin = build_content_prompt(
        topic="Building in public",
        platform="linkedin",
        persona_data={"tone": "professional"},
    )
    instagram = build_content_prompt(
        topic="Building in public",
        platform="instagram_personal",
        persona_data={"tone": "casual"},
    )
    # They should be different — different platform requirements
    assert linkedin != instagram, "Platform prompts should differ"


def test_empty_topic_handled():
    """Builder should handle empty topic gracefully."""
    from persona_engine.prompt_builder import build_content_prompt
    try:
        result = build_content_prompt(topic="", platform="linkedin", persona_data={})
        assert result is not None  # Should return something or raise
    except (ValueError, TypeError):
        pass  # Raising for empty topic is acceptable


if __name__ == "__main__":
    test_build_prompt_for_linkedin()
    test_build_prompt_for_instagram()
    test_empty_topic_handled()
    print("✅ All prompt_builder tests passed")

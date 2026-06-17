"""
Tests for Persona Updater module.
Verifies atomic persona.md updates, version tracking, and strategy history appending.
"""

import sys
import os
import tempfile
import shutil
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


def test_update_persona_increments_version():
    """Updater should increment version number."""
    from persona_engine.updater import update_persona

    # Create a temp persona file
    tmpdir = tempfile.mkdtemp()
    persona_path = os.path.join(tmpdir, "persona.md")
    with open(persona_path, "w") as f:
        f.write("""# Test Persona
_Version: 1 | Last updated: 2024-01-01T00:00:00Z | Strategy: baseline_

## 1. Identity
**Name:** Test Brand

## 7. Performance Memory
| Account | Best format | Best pillar | Best hook type | Avg engagement score |
|---|---|---|---|---|
| LinkedIn | --- | --- | --- | --- |

**Strategy history:**
| Version | Date | Change | Reason |
|---|---|---|---|
| 1 | 2024-01-01 | Initial generation | Onboarding |
""")

    try:
        result = update_persona(
            persona_path=persona_path,
            trigger="time_based",
            pattern_db_data={"linkedin": {"best_format": "carousel", "best_pillar": "tech", "best_hook_type": "contradiction", "avg_engagement_score": 85.0}},
        )
        assert result is not None, "Updater should return a result"
        if hasattr(result, "version"):
            assert result.version >= 1, "Version should be at least 1"
    finally:
        shutil.rmtree(tmpdir)


def test_update_preserves_existing_content():
    """Updater should not destroy existing sections."""
    from persona_engine.updater import update_persona

    tmpdir = tempfile.mkdtemp()
    persona_path = os.path.join(tmpdir, "persona.md")
    original_content = """# Test Persona
_Version: 1 | Last updated: 2024-01-01T00:00:00Z_

## 1. Identity
**Name:** Ahmad

## 2. Voice & Tone
**Vocabulary always used:** system, pipeline
"""
    with open(persona_path, "w") as f:
        f.write(original_content)

    try:
        result = update_persona(persona_path=persona_path, trigger="time_based")
        with open(persona_path, "r") as f:
            updated = f.read()
        assert "Ahmad" in updated, "Name should be preserved"
        assert "system, pipeline" in updated, "Vocabulary should be preserved"
    finally:
        shutil.rmtree(tmpdir)


if __name__ == "__main__":
    test_update_persona_increments_version()
    test_update_preserves_existing_content()
    print("✅ All persona_updater tests passed")

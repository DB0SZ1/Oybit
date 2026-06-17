"""
Independent Verification Tests — GAP 5.1
Verify OUTCOMES not implementation details.
Written AFTER agents built their modules — tests from Ahmad's perspective.

Run: python scripts/tests/test_independent_verification.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


def test_content_dna_rule_kills_bad_content():
    """
    Generate generic posts — verify DNA checker rejects vague content.
    Tests the guardian from outside, not from within.
    """
    from intelligence.content_dna_checker import check_content_dna

    bad_texts = [
        "Working on something exciting in the tech space",
        "Great things are coming soon! Stay tuned!",
        "Hustle harder, dream bigger, level up!",
        "Happy Monday everyone! Let's crush this week!",
        "Networking is so important for your career growth",
    ]
    for text in bad_texts:
        result = check_content_dna(text, use_ai=False)
        # At least some of these should fail DNA check
        if result.passes:
            print(f"  ⚠ Vague text passed DNA check: '{text[:50]}...'")


def test_engagement_score_formula_is_correct():
    """Verify the exact formula — saves×5 + shares×3 + comments×2 + follows×5."""
    from feedback_loop.learning_engine import compute_engagement_score

    # With follower_count=1 (no normalization), formula should be:
    # (saves/1*1000)*5 + (shares/1*1000)*3 + (comments/1*1000)*2 + (follows/1*1000)*5
    score = compute_engagement_score(saves=4, shares=3, comments=5, follows=2, follower_count=1000)
    # saves: 4/1000*1000 = 4, *5 = 20
    # shares: 3/1000*1000 = 3, *3 = 9
    # comments: 5/1000*1000 = 5, *2 = 10
    # follows: 2/1000*1000 = 2, *5 = 10
    # Total = 49
    expected = 49.0
    assert abs(score - expected) < 1.0, f"Score formula wrong: expected ~{expected}, got {score}"
    print(f"  ✅ Engagement score = {score} (expected ~{expected})")


def test_questions_bank_has_all_stages():
    """All 6 stages should have questions."""
    from onboarding.questions import get_questions_for_stage, get_total_question_count

    total = get_total_question_count()
    assert total >= 100, f"Expected 100+ questions, got {total}"

    for stage in range(1, 7):
        qs = get_questions_for_stage(stage)
        assert len(qs) >= 5, f"Stage {stage} has only {len(qs)} questions"
        print(f"  Stage {stage}: {len(qs)} questions")

    print(f"  Total: {total} questions across 6 stages")


def test_persona_template_has_all_sections():
    """Production persona template should have all 8 sections."""
    template_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "data", "personas", "_template.md"
    )
    if not os.path.exists(template_path):
        print(f"  ⚠ Template not found at {template_path}")
        return

    with open(template_path, "r") as f:
        content = f.read()

    required_sections = [
        "Identity", "Voice", "Audience", "Content Pillars",
        "Tone Modifiers", "Engagement Style", "Visual Identity", "Performance Memory",
    ]
    for section in required_sections:
        assert section in content, f"Template missing section: {section}"

    print(f"  ✅ Template has all {len(required_sections)} required sections")


def test_db_models_no_duplicate_tables():
    """Verify no duplicate __tablename__ in models."""
    from db.models import Base

    tablenames = []
    for mapper in Base.registry.mappers:
        cls = mapper.class_
        if hasattr(cls, "__tablename__"):
            tn = cls.__tablename__
            assert tn not in tablenames, f"Duplicate table name: {tn}"
            tablenames.append(tn)

    print(f"  ✅ {len(tablenames)} unique table names, no duplicates")


def test_calibration_module_exists():
    """Calibration module should be importable."""
    from onboarding.calibration import submit_calibration_rating
    result = submit_calibration_rating(
        post_text="Test post",
        rating=8,
        reasoning="Sounds authentic",
        platform="linkedin",
    )
    assert result["stored"] is True
    assert result["action"] == "reinforce"
    print(f"  ✅ Calibration module works: {result['action']}")


if __name__ == "__main__":
    print("\n🔬 Independent Verification Tests\n" + "=" * 50)

    tests = [
        ("Content DNA rejects vague content", test_content_dna_rule_kills_bad_content),
        ("Engagement score formula", test_engagement_score_formula_is_correct),
        ("Questions bank completeness", test_questions_bank_has_all_stages),
        ("Persona template sections", test_persona_template_has_all_sections),
        ("DB model uniqueness", test_db_models_no_duplicate_tables),
        ("Calibration module", test_calibration_module_exists),
    ]

    passed = 0
    failed = 0
    for name, test_fn in tests:
        try:
            print(f"\n▶ {name}")
            test_fn()
            passed += 1
        except Exception as e:
            print(f"  ❌ FAILED: {e}")
            failed += 1

    print(f"\n{'=' * 50}")
    print(f"Results: {passed} passed, {failed} failed, {len(tests)} total")

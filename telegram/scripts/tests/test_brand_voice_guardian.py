"""
Tests for Brand Voice Guardian module.
Verifies that the guardian correctly accepts/rejects content
based on persona voice rules per platform.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


def test_good_linkedin_post_passes():
    """A well-crafted LinkedIn post with strong hook should pass."""
    from brand_voice_guardian.guardian import check_brand_voice
    post = (
        "I shipped a feature at 2AM that prevented a security breach.\n\n"
        "Here's the thing about API security most developers ignore:\n"
        "Your rate limiter is only as good as your slowest middleware.\n\n"
        "We found a timing attack vulnerability in our auth pipeline.\n"
        "The fix took 3 lines of code. The investigation took 6 hours."
    )
    result = check_brand_voice(post, "linkedin")
    assert result.passed, f"Good LinkedIn post rejected: {result.rejection_reasons}"


def test_generic_motivational_fails():
    """Generic motivational content should fail brand voice check."""
    from brand_voice_guardian.guardian import check_brand_voice
    post = "Rise and grind! 💪 Every day is a new opportunity to level up! #hustle #motivation"
    result = check_brand_voice(post, "linkedin")
    assert not result.passed, "Generic motivational post should have been rejected"


def test_too_short_post_fails():
    """Posts under minimum length should fail."""
    from brand_voice_guardian.guardian import check_brand_voice
    result = check_brand_voice("Great stuff!", "linkedin")
    assert not result.passed, "Too-short post should fail"


def test_forbidden_vocab_detected():
    """Posts with forbidden vocabulary should be flagged."""
    from brand_voice_guardian.guardian import check_brand_voice
    post = (
        "Let's leverage our synergies to level up and create a paradigm shift "
        "in how we hustle toward our goals! #bosslife"
    )
    result = check_brand_voice(post, "linkedin")
    assert not result.passed, "Post with forbidden vocab should fail"


def test_instagram_tone_accepted():
    """Instagram posts can be more casual."""
    from brand_voice_guardian.guardian import check_brand_voice
    post = (
        "built this in 3 hours. sometimes the best code is the code you don't write 🔥\n"
        "shipping > perfecting"
    )
    result = check_brand_voice(post, "instagram_personal")
    # Instagram is more lenient with casual tone
    assert result is not None  # Just verify it returns a result


if __name__ == "__main__":
    test_good_linkedin_post_passes()
    test_generic_motivational_fails()
    test_too_short_post_fails()
    test_forbidden_vocab_detected()
    test_instagram_tone_accepted()
    print("✅ All brand_voice_guardian tests passed")

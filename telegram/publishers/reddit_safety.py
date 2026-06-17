"""
Oybit — Reddit Anti-Detection (GAP 5.4)
Humanizes Reddit posting to avoid bot detection.
"""
import random
import time
import logging
import re

logger = logging.getLogger(__name__)

# Subreddit engagement history
_sub_history = {}

def humanize_delay() -> float:
    """Return a random delay between 45-180 seconds to simulate human behavior."""
    return random.uniform(45, 180)

def vary_title(title: str) -> str:
    """Apply minor randomized variations to post titles."""
    variations = [
        lambda t: t,  # no change
        lambda t: t.lower() if random.random() > 0.7 else t,
        lambda t: t + "?" if not t.endswith("?") and random.random() > 0.8 else t,
        lambda t: t.rstrip(".") if t.endswith(".") else t,
    ]
    return random.choice(variations)(title)

def should_comment_first(subreddit: str) -> bool:
    """
    Reddit anti-detection: comment on 2-3 posts in a subreddit before posting.
    Returns True if we should comment first, False if we've already engaged enough.
    """
    count = _sub_history.get(subreddit, 0)
    if count < 2:
        return True
    return False

def record_engagement(subreddit: str):
    """Record that we engaged (commented) in a subreddit."""
    _sub_history[subreddit] = _sub_history.get(subreddit, 0) + 1

def check_karma_requirements(subreddit_rules: dict) -> bool:
    """Check if account meets subreddit karma/age requirements."""
    # This would check against actual Reddit account data
    min_karma = subreddit_rules.get("min_karma", 0)
    min_age_days = subreddit_rules.get("min_age_days", 0)
    return True  # Placeholder — real check against Reddit API

def sanitize_reddit_text(text: str) -> str:
    """Remove marketing-sounding language that triggers Reddit spam filters."""
    spam_phrases = [
        r'\bcheck out\b', r'\bfollow me\b', r'\blink in bio\b',
        r'\bsubscribe\b', r'\bmy product\b', r'\bgame.changer\b',
        r'\blimited time\b', r'\bact now\b', r'\bfree trial\b'
    ]
    result = text
    for pattern in spam_phrases:
        result = re.sub(pattern, '', result, flags=re.IGNORECASE)
    return result.strip()

"""
Comment Sentiment Analyzer — Scores comment quality using keyword-based analysis.
Replaces raw comment count with a weighted quality score in the engagement formula.
Zero API cost — uses keyword matching exclusively.
"""

from enum import Enum
from backend.logger import get_logger

logger = get_logger("analytics.comment_sentiment")


class CommentQuality(str, Enum):
    HIGH = "high"       # Substantive engagement: questions, stories, debates
    MEDIUM = "medium"   # Basic engagement: agreement, short compliments
    LOW = "low"         # Low-value: emoji-only, "nice", single-word
    SPAM = "spam"       # Bot/spam: follow4follow, promo links


# Keyword scoring rules
HIGH_QUALITY_SIGNALS = [
    "how do", "how can", "what if", "have you tried", "in my experience",
    "I built", "I shipped", "I tried", "at my company", "we found",
    "disagree because", "counterpoint", "alternatively", "great point but",
    "this reminds me", "similar situation", "question about",
    "what stack", "what tools", "recommendation",
]

MEDIUM_QUALITY_SIGNALS = [
    "agree", "so true", "well said", "great post", "love this",
    "thank you", "thanks for sharing", "insightful", "helpful",
    "needed this", "saved", "bookmarked", "following",
    "absolutely", "100%", "facts", "exactly",
]

LOW_QUALITY_SIGNALS = [
    "nice", "good", "cool", "wow", "ok", "great",
]

SPAM_SIGNALS = [
    "follow me", "check my profile", "dm me", "follow back",
    "make money", "click link", "visit my", "free followers",
    "crypto", "forex", "binary options", "💰", "🔥 DM",
    "http://", "https://bit.ly", "t.me/",
]


def classify_comment(comment_text: str) -> CommentQuality:
    """
    Classify a single comment by quality.

    Args:
        comment_text: the comment text

    Returns:
        CommentQuality enum value
    """
    text = comment_text.lower().strip()

    if not text or len(text) < 2:
        return CommentQuality.LOW

    # Check spam first (highest priority)
    if any(signal in text for signal in SPAM_SIGNALS):
        return CommentQuality.SPAM

    # Check for emoji-only comments
    import re
    text_no_emoji = re.sub(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F900-\U0001F9FF\u2600-\u26FF\u2700-\u27BF]', '', text).strip()
    if not text_no_emoji or len(text_no_emoji) < 3:
        return CommentQuality.LOW

    # Score based on signals
    high_matches = sum(1 for s in HIGH_QUALITY_SIGNALS if s in text)
    medium_matches = sum(1 for s in MEDIUM_QUALITY_SIGNALS if s in text)
    low_matches = sum(1 for s in LOW_QUALITY_SIGNALS if s == text.rstrip("!."))

    # Length-based bonus (longer = usually higher quality)
    word_count = len(text.split())
    if word_count > 20:
        high_matches += 1
    elif word_count < 3:
        low_matches += 1

    if high_matches > 0:
        return CommentQuality.HIGH
    elif medium_matches > 0:
        return CommentQuality.MEDIUM
    elif low_matches > 0 or word_count < 4:
        return CommentQuality.LOW
    else:
        return CommentQuality.MEDIUM  # Default for unclassified medium-length comments


# Quality weights for engagement formula
QUALITY_WEIGHTS = {
    CommentQuality.HIGH: 3.0,
    CommentQuality.MEDIUM: 1.0,
    CommentQuality.LOW: 0.3,
    CommentQuality.SPAM: 0.0,
}


def compute_comment_quality_score(comments: list) -> dict:
    """
    Compute a weighted comment quality score for a post.
    Replaces raw comment_count in the engagement formula.

    Args:
        comments: list of comment text strings

    Returns:
        dict with quality_score, breakdown, and raw_count
    """
    if not comments:
        return {
            "quality_score": 0.0,
            "raw_count": 0,
            "breakdown": {},
            "weighted_count": 0.0,
        }

    breakdown = {q.value: 0 for q in CommentQuality}
    weighted_total = 0.0

    for comment in comments:
        quality = classify_comment(comment)
        breakdown[quality.value] += 1
        weighted_total += QUALITY_WEIGHTS[quality]

    quality_score = weighted_total / max(len(comments), 1)

    result = {
        "quality_score": round(quality_score, 2),
        "raw_count": len(comments),
        "weighted_count": round(weighted_total, 1),
        "breakdown": breakdown,
        "spam_rate": round(breakdown[CommentQuality.SPAM.value] / max(len(comments), 1), 2),
    }

    logger.info("Comment quality scored", extra=result)
    return result

"""
Audience Quality Scorer — Measures follower relevance to Ahmad's target audience.
Target: Nigerian/African developers, founders, tech professionals.
Uses bio keywords and location matching (zero API cost).
"""

from logger import get_logger

logger = get_logger("analytics.audience_quality")

# Target audience signals (weighted)
TARGET_BIO_KEYWORDS = {
    # High relevance (3.0 weight)
    "developer": 3.0, "engineer": 3.0, "founder": 3.0, "cto": 3.0,
    "builder": 3.0, "indie hacker": 3.0, "building": 3.0, "shipping": 3.0,
    "startup": 3.0, "tech lead": 3.0, "software": 3.0, "fullstack": 3.0,

    # Medium relevance (2.0 weight)
    "product": 2.0, "design": 2.0, "data": 2.0, "ai": 2.0,
    "machine learning": 2.0, "devops": 2.0, "frontend": 2.0,
    "backend": 2.0, "mobile": 2.0, "web": 2.0, "cloud": 2.0,
    "open source": 2.0, "api": 2.0, "saas": 2.0, "fintech": 2.0,

    # Low relevance (1.0 weight)
    "tech": 1.0, "digital": 1.0, "innovation": 1.0, "creative": 1.0,
    "entrepreneur": 1.0, "investor": 1.0, "mentor": 1.0,
}

TARGET_LOCATIONS = {
    # Primary (3.0 weight)
    "nigeria": 3.0, "lagos": 3.0, "abuja": 3.0, "nairobi": 3.0,
    "accra": 3.0, "kigali": 3.0, "cape town": 3.0, "johannesburg": 3.0,

    # Secondary (2.0 weight)
    "africa": 2.0, "west africa": 2.0, "east africa": 2.0,
    "london": 2.0, "dubai": 2.0,

    # Tertiary (1.0 weight)
    "san francisco": 1.0, "new york": 1.0, "berlin": 1.0,
    "bangalore": 1.0, "toronto": 1.0,
}

# Negative signals (reduce score)
BOT_SIGNALS = [
    "follow4follow", "f4f", "l4l", "crypto", "forex",
    "binary options", "make money fast", "dm for",
]


def score_follower_quality(profile: dict) -> dict:
    """
    Score a single follower's relevance to Ahmad's audience.

    Args:
        profile: dict with bio, location, followers_count, following_count

    Returns:
        dict with relevance_score (0-10), breakdown, and flags
    """
    bio = (profile.get("bio") or "").lower()
    location = (profile.get("location") or "").lower()
    followers = profile.get("followers_count", 0)
    following = profile.get("following_count", 0)

    # Bio keyword scoring
    bio_score = 0.0
    matched_keywords = []
    for keyword, weight in TARGET_BIO_KEYWORDS.items():
        if keyword in bio:
            bio_score += weight
            matched_keywords.append(keyword)

    # Location scoring
    location_score = 0.0
    for loc, weight in TARGET_LOCATIONS.items():
        if loc in location:
            location_score = max(location_score, weight)
            break

    # Bot detection
    is_bot = any(signal in bio for signal in BOT_SIGNALS)
    if following > 5000 and followers < 100:
        is_bot = True
    if profile.get("is_default_avatar", False) and followers < 10:
        is_bot = True

    if is_bot:
        return {
            "relevance_score": 0.0,
            "bio_score": 0.0,
            "location_score": 0.0,
            "is_bot": True,
            "matched_keywords": [],
        }

    # Normalize and combine
    bio_normalized = min(bio_score / 6.0, 1.0)  # Max ~6 points from keywords
    location_normalized = location_score / 3.0

    relevance_score = round((bio_normalized * 6 + location_normalized * 3 + 1) * (1 if not is_bot else 0), 1)
    relevance_score = min(relevance_score, 10.0)

    return {
        "relevance_score": relevance_score,
        "bio_score": round(bio_score, 1),
        "location_score": round(location_score, 1),
        "is_bot": False,
        "matched_keywords": matched_keywords[:5],
    }


def compute_audience_quality(follower_profiles: list) -> dict:
    """
    Compute aggregate audience quality score from a sample of followers.

    Args:
        follower_profiles: list of profile dicts

    Returns:
        dict with avg_quality, bot_rate, top_segments
    """
    if not follower_profiles:
        return {"avg_quality": 0.0, "sample_size": 0}

    scores = []
    bot_count = 0
    keyword_freq = {}

    for profile in follower_profiles:
        result = score_follower_quality(profile)
        scores.append(result["relevance_score"])
        if result["is_bot"]:
            bot_count += 1
        for kw in result.get("matched_keywords", []):
            keyword_freq[kw] = keyword_freq.get(kw, 0) + 1

    avg_quality = sum(scores) / len(scores)

    # Top audience segments
    top_segments = sorted(keyword_freq.items(), key=lambda x: x[1], reverse=True)[:5]

    result = {
        "avg_quality": round(avg_quality, 2),
        "sample_size": len(follower_profiles),
        "bot_rate": round(bot_count / len(follower_profiles), 2),
        "high_quality_pct": round(sum(1 for s in scores if s >= 5) / len(scores), 2),
        "top_segments": dict(top_segments),
    }

    logger.info("Audience quality computed", extra=result)
    return result

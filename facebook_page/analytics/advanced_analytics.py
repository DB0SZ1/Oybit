"""
Oybit — Advanced Analytics (GAPS_FINAL GAPs 3.1–3.3)
Comment sentiment analysis, profile visits tracking, audience demographic scoring.
"""
import logging
import re
from datetime import datetime

logger = logging.getLogger(__name__)

# ── GAP 3.1: Comment Sentiment Analysis ───────────────────────
POSITIVE_WORDS = {"great", "amazing", "love", "awesome", "fantastic", "brilliant", "helpful", 
                  "insightful", "agree", "inspired", "thank", "congratulations", "well done",
                  "beautiful", "perfect", "excellent", "fire", "goat", "king", "queen"}

NEGATIVE_WORDS = {"bad", "terrible", "disagree", "wrong", "hate", "awful", "spam", "scam",
                  "boring", "fake", "cringe", "worst", "disappointed", "misleading", "trash"}

def analyze_sentiment(text: str) -> dict:
    """Simple keyword-based sentiment analysis for comments."""
    words = set(re.findall(r'\w+', text.lower()))
    
    pos_count = len(words & POSITIVE_WORDS)
    neg_count = len(words & NEGATIVE_WORDS)
    
    if pos_count > neg_count:
        sentiment = "positive"
        score = min(1.0, pos_count * 0.3)
    elif neg_count > pos_count:
        sentiment = "negative"
        score = max(-1.0, -neg_count * 0.3)
    else:
        sentiment = "neutral"
        score = 0.0
    
    return {"sentiment": sentiment, "score": round(score, 2), "positive_signals": pos_count, "negative_signals": neg_count}

def batch_analyze_comments(comments: list[dict]) -> dict:
    """Analyze sentiment for a batch of comments on a post."""
    results = {"positive": 0, "negative": 0, "neutral": 0, "avg_score": 0}
    scores = []
    
    for comment in comments:
        analysis = analyze_sentiment(comment.get("text", ""))
        results[analysis["sentiment"]] += 1
        scores.append(analysis["score"])
    
    results["avg_score"] = round(sum(scores) / len(scores), 2) if scores else 0
    results["total"] = len(comments)
    return results


# ── GAP 3.2: Profile Visits Tracking ──────────────────────────
def fetch_profile_visits_instagram(ig_user_id: str, access_token: str) -> dict:
    """Fetch profile visit metrics from Instagram Insights API."""
    import httpx
    
    url = f"https://graph.facebook.com/v21.0/{ig_user_id}/insights"
    params = {
        "metric": "profile_views",
        "period": "day",
        "access_token": access_token
    }
    
    try:
        resp = httpx.get(url, params=params, timeout=15)
        if resp.status_code == 200:
            data = resp.json().get("data", [])
            if data:
                values = data[0].get("values", [])
                return {"profile_views": [v.get("value", 0) for v in values], "period": "daily"}
        return {"profile_views": [], "error": f"HTTP {resp.status_code}"}
    except Exception as e:
        return {"profile_views": [], "error": str(e)}


# ── GAP 3.3: Audience Demographic Quality Scoring ─────────────
def score_audience_quality(demographics: dict) -> float:
    """
    Score audience quality 0-100 based on demographic alignment.
    Higher score = audience matches the target persona's ideal follower.
    """
    score = 50.0  # Base score
    
    # Age distribution (25-44 is ideal for business/tech content)
    age_25_34 = demographics.get("age_25_34_pct", 0)
    age_35_44 = demographics.get("age_35_44_pct", 0)
    target_age_pct = age_25_34 + age_35_44
    score += (target_age_pct - 40) * 0.5  # Bonus if >40% in target age
    
    # Location (Nigeria + global tech hubs)
    nigeria_pct = demographics.get("nigeria_pct", 0)
    if nigeria_pct > 30:
        score += 10
    
    # Gender balance (for business content, balanced is good)
    male_pct = demographics.get("male_pct", 50)
    if 35 <= male_pct <= 65:
        score += 5  # Bonus for balanced audience
    
    # Engagement authenticity (bot detection)
    if demographics.get("suspicious_accounts_pct", 0) > 10:
        score -= 15
    
    return max(0, min(100, round(score, 1)))

"""
Oybit — Analytics Scorer
Computes engagement score and tags posts.
"""
from analytics.aggregator import compute_engagement_score


def score_post_analytics(analytics_record) -> float:
    """
    Compute engagement score from a PostAnalytics record.
    Formula: saves*5 + shares*3 + comments*2 + follows*5
    """
    return compute_engagement_score(
        saves=analytics_record.saves or 0,
        shares=analytics_record.shares or 0,
        comments=analytics_record.comments or 0,
        follows=analytics_record.follows or 0
    )

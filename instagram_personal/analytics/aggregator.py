"""
Oybit — Analytics Aggregator
Pulls metrics from all 4 platform APIs after 48h.
Creates PostAnalytics records and computes engagement scores.
"""
import os
import logging
from datetime import datetime, timedelta

import httpx

from db.models import Post, PostAnalytics, get_session
from token_store.store import get_token

logger = logging.getLogger(__name__)

META_BASE_URL = "https://graph.facebook.com/v19.0"
LINKEDIN_BASE_URL = "https://api.linkedin.com/v2"


def compute_engagement_score(saves: int, shares: int, comments: int, follows: int) -> float:
    """Engagement score formula as defined in spec."""
    return saves * 5 + shares * 3 + comments * 2 + follows * 5


def aggregate_post_analytics(post_id: int, account: str, platform_post_id: str,
                             engine=None, http_client: httpx.Client = None) -> dict:
    """
    Pull analytics for a single post from its platform API.

    Returns dict with: reach, impressions, likes, comments, shares, saves, follows, clicks
    """
    metrics = {
        "reach": 0, "impressions": 0, "likes": 0, "comments": 0,
        "shares": 0, "saves": 0, "follows": 0, "clicks": 0
    }

    client = http_client or httpx.Client(timeout=30)

    try:
        if account in ("instagram_personal", "instagram_brand"):
            metrics = _pull_instagram_metrics(platform_post_id, account, client)
        elif account == "facebook":
            metrics = _pull_facebook_metrics(platform_post_id, client)
        elif account == "linkedin":
            metrics = _pull_linkedin_metrics(platform_post_id, client)
    except Exception as e:
        logger.error(f"Failed to pull analytics for post {post_id} ({account}): {e}")
        raise

    return metrics


def _pull_instagram_metrics(media_id: str, account: str, client: httpx.Client) -> dict:
    """Pull Instagram post insights."""
    token = get_token(account, "access_token") or os.getenv(
        f"INSTAGRAM_{'PERSONAL' if account == 'instagram_personal' else 'BRAND'}_ACCESS_TOKEN", "")
    if not token:
        raise ValueError(f"No token for {account}")

    resp = client.get(f"{META_BASE_URL}/{media_id}/insights", params={
        "metric": "reach,impressions,likes,comments,shares,saved",
        "access_token": token
    })
    resp.raise_for_status()
    data = resp.json().get("data", [])

    metrics = {"reach": 0, "impressions": 0, "likes": 0, "comments": 0,
               "shares": 0, "saves": 0, "follows": 0, "clicks": 0}

    for metric in data:
        name = metric.get("name", "")
        values = metric.get("values", [{}])
        value = values[0].get("value", 0) if values else 0
        if name == "reach":
            metrics["reach"] = value
        elif name == "impressions":
            metrics["impressions"] = value
        elif name == "likes":
            metrics["likes"] = value
        elif name == "comments":
            metrics["comments"] = value
        elif name == "shares":
            metrics["shares"] = value
        elif name == "saved":
            metrics["saves"] = value

    return metrics


def _pull_facebook_metrics(post_id: str, client: httpx.Client) -> dict:
    """Pull Facebook post insights."""
    token = get_token("facebook", "access_token") or os.getenv("FACEBOOK_PAGE_ACCESS_TOKEN", "")
    if not token:
        raise ValueError("No Facebook token")

    resp = client.get(f"{META_BASE_URL}/{post_id}/insights", params={
        "metric": "post_impressions,post_reach,post_reactions_by_type_total,post_clicks,post_shares",
        "access_token": token
    })
    resp.raise_for_status()
    data = resp.json().get("data", [])

    metrics = {"reach": 0, "impressions": 0, "likes": 0, "comments": 0,
               "shares": 0, "saves": 0, "follows": 0, "clicks": 0}

    for metric in data:
        name = metric.get("name", "")
        values = metric.get("values", [{}])
        value = values[0].get("value", 0) if values else 0
        if name == "post_reach":
            metrics["reach"] = value
        elif name == "post_impressions":
            metrics["impressions"] = value
        elif name == "post_clicks":
            metrics["clicks"] = value
        elif name == "post_shares":
            metrics["shares"] = value if isinstance(value, int) else 0

    return metrics


def _pull_linkedin_metrics(post_urn: str, client: httpx.Client) -> dict:
    """Pull LinkedIn post social actions."""
    token = get_token("linkedin", "access_token") or os.getenv("LINKEDIN_ACCESS_TOKEN", "")
    if not token:
        raise ValueError("No LinkedIn token")

    headers = {
        "Authorization": f"Bearer {token}",
        "X-Restli-Protocol-Version": "2.0.0"
    }

    resp = client.get(f"{LINKEDIN_BASE_URL}/socialActions/{post_urn}", headers=headers)
    resp.raise_for_status()
    data = resp.json()

    return {
        "reach": 0,
        "impressions": 0,
        "likes": data.get("likesSummary", {}).get("totalLikes", 0),
        "comments": data.get("commentsSummary", {}).get("totalFirstLevelComments", 0),
        "shares": 0,
        "saves": 0,
        "follows": 0,
        "clicks": 0
    }


def run_aggregation(engine=None, http_client: httpx.Client = None):
    """
    Run aggregation for all published posts older than 48h that haven't been collected yet.
    """
    session = get_session(engine)
    try:
        cutoff = datetime.utcnow() - timedelta(hours=48)
        posts = session.query(Post).filter(
            Post.status == "published",
            Post.published_at != None,
            Post.published_at <= cutoff,
            Post.analytics_collected == False,
            Post.platform_post_id != None
        ).all()

        logger.info(f"Found {len(posts)} posts to aggregate analytics for")

        for post in posts:
            try:
                metrics = aggregate_post_analytics(
                    post.id, post.account, post.platform_post_id,
                    engine, http_client
                )

                engagement = compute_engagement_score(
                    metrics["saves"], metrics["shares"],
                    metrics["comments"], metrics["follows"]
                )

                analytics = PostAnalytics(
                    post_id=post.id,
                    account=post.account,
                    reach=metrics["reach"],
                    impressions=metrics["impressions"],
                    likes=metrics["likes"],
                    comments=metrics["comments"],
                    shares=metrics["shares"],
                    saves=metrics["saves"],
                    follows=metrics["follows"],
                    clicks=metrics["clicks"],
                    engagement_score=engagement
                )
                session.add(analytics)

                post.analytics_collected = True
                post.engagement_score = engagement
                session.commit()

                logger.info(f"Aggregated analytics for post {post.id}: score={engagement}")
            except Exception as e:
                logger.error(f"Failed to aggregate post {post.id}: {e}")
                session.rollback()
                continue

    finally:
        session.close()

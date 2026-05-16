"""
Oybit — Reply Monitor
Polls comment feeds for all 4 accounts.
Classifies comment type and saves to Reply table.
"""
import os
import logging
from datetime import datetime

import httpx

from backend.db.models import Reply, get_session
from backend.token_store.store import get_token

logger = logging.getLogger(__name__)

META_BASE_URL = "https://graph.facebook.com/v19.0"
LINKEDIN_BASE_URL = "https://api.linkedin.com/v2"

SPAM_KEYWORDS = [
    "buy followers", "get followers", "dm for promo", "check my bio",
    "click the link", "free money", "giveaway winner", "bit.ly",
    "earn money", "work from home scam"
]

COMMENT_TYPE_KEYWORDS = {
    "praise": ["great", "amazing", "awesome", "love this", "well done", "brilliant", "incredible", "fire", "🔥", "💯"],
    "question": ["how", "what", "why", "when", "where", "can you", "could you", "?"],
    "criticism": ["wrong", "disagree", "bad", "terrible", "misleading", "false", "incorrect", "no offense but"],
}


def classify_comment(text: str) -> str:
    """Classify comment type based on keywords."""
    lower = text.lower()

    # Check spam first
    for keyword in SPAM_KEYWORDS:
        if keyword in lower:
            return "spam"

    # Check question (? is strong signal)
    if "?" in text:
        return "question"

    # Check other types
    for ctype, keywords in COMMENT_TYPE_KEYWORDS.items():
        for kw in keywords:
            if kw in lower:
                return ctype

    return "debate"  # default


def poll_instagram_comments(media_id: str, account: str,
                            engine=None, http_client: httpx.Client = None) -> list[dict]:
    """Poll Instagram comments for a media post."""
    token = get_token(account, "access_token") or ""
    if not token:
        return []

    client = http_client or httpx.Client(timeout=30)
    resp = client.get(f"{META_BASE_URL}/{media_id}/comments", params={
        "fields": "id,text,username,timestamp",
        "access_token": token
    })
    resp.raise_for_status()
    return resp.json().get("data", [])


def poll_facebook_comments(post_id: str,
                           engine=None, http_client: httpx.Client = None) -> list[dict]:
    """Poll Facebook comments for a post."""
    token = get_token("facebook", "access_token") or ""
    if not token:
        return []

    client = http_client or httpx.Client(timeout=30)
    resp = client.get(f"{META_BASE_URL}/{post_id}/comments", params={
        "fields": "id,message,from,created_time",
        "access_token": token
    })
    resp.raise_for_status()
    return resp.json().get("data", [])


def poll_linkedin_comments(post_urn: str,
                           engine=None, http_client: httpx.Client = None) -> list[dict]:
    """Poll LinkedIn comments for a post."""
    token = get_token("linkedin", "access_token") or ""
    if not token:
        return []

    client = http_client or httpx.Client(timeout=30)
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Restli-Protocol-Version": "2.0.0"
    }
    resp = client.get(f"{LINKEDIN_BASE_URL}/socialActions/{post_urn}/comments", headers=headers)
    resp.raise_for_status()
    return resp.json().get("elements", [])


def process_comments(post_id: int, account: str, comments: list[dict],
                     engine=None) -> list[Reply]:
    """
    Process raw comments: classify, skip spam, save new ones to Reply table.
    Already-seen comments (by platform_comment_id) are NOT duplicated.
    """
    session = get_session(engine)
    new_replies = []

    try:
        for comment in comments:
            # Normalize comment data across platforms
            if account in ("instagram_personal", "instagram_brand"):
                platform_id = comment.get("id", "")
                text = comment.get("text", "")
            elif account == "facebook":
                platform_id = comment.get("id", "")
                text = comment.get("message", "")
            elif account == "linkedin":
                platform_id = comment.get("$URN", comment.get("id", ""))
                text = comment.get("message", {}).get("text", "") if isinstance(comment.get("message"), dict) else str(comment.get("message", ""))
            else:
                continue

            if not platform_id or not text:
                continue

            # Check if already seen
            existing = session.query(Reply).filter_by(
                platform_comment_id=platform_id
            ).first()
            if existing:
                continue

            # Classify
            comment_type = classify_comment(text)

            # Skip spam
            if comment_type == "spam":
                logger.info(f"Skipping spam comment: {text[:50]}")
                continue

            # Create Reply record
            reply = Reply(
                post_id=post_id,
                account=account,
                platform_comment_id=platform_id,
                comment_text=text,
                comment_type=comment_type,
                status="pending_approval"
            )
            session.add(reply)
            new_replies.append(reply)

        session.commit()
        return new_replies

    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

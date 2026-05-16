"""
Oybit — Reply Sender
Sends approved replies to the correct platform API.
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


def send_reply(reply_id: int, engine=None, http_client: httpx.Client = None) -> dict:
    """
    Send an approved reply to the correct platform.

    Args:
        reply_id: Reply record ID
        engine: DB engine
        http_client: injectable HTTP client

    Returns:
        dict with success status
    """
    session = get_session(engine)
    try:
        reply = session.query(Reply).filter_by(id=reply_id).first()
        if not reply:
            raise ValueError(f"Reply {reply_id} not found")

        if not reply.draft_reply:
            raise ValueError(f"Reply {reply_id} has no draft to send")

        client = http_client or httpx.Client(timeout=30)
        result = {}

        if reply.account in ("instagram_personal", "instagram_brand"):
            result = _send_instagram_reply(reply, client)
        elif reply.account == "facebook":
            result = _send_facebook_reply(reply, client)
        elif reply.account == "linkedin":
            result = _send_linkedin_reply(reply, client)
        else:
            raise ValueError(f"Unknown account: {reply.account}")

        # Update Reply record
        reply.status = "sent"
        reply.sent_at = datetime.utcnow()
        session.commit()

        logger.info(f"Sent reply {reply_id} to {reply.account}")
        return {"success": True, **result}

    except Exception as e:
        logger.error(f"Failed to send reply {reply_id}: {e}")
        session.rollback()
        raise
    finally:
        session.close()


def _send_instagram_reply(reply: Reply, client: httpx.Client) -> dict:
    """Send reply to Instagram comment."""
    token = get_token(reply.account, "access_token") or ""
    if not token:
        raise ValueError(f"No token for {reply.account}")

    resp = client.post(f"{META_BASE_URL}/{reply.platform_comment_id}/replies", params={
        "message": reply.draft_reply,
        "access_token": token
    })
    resp.raise_for_status()
    return resp.json()


def _send_facebook_reply(reply: Reply, client: httpx.Client) -> dict:
    """Send reply to Facebook comment."""
    token = get_token("facebook", "access_token") or ""
    if not token:
        raise ValueError("No Facebook token")

    resp = client.post(f"{META_BASE_URL}/{reply.platform_comment_id}/comments", params={
        "message": reply.draft_reply,
        "access_token": token
    })
    resp.raise_for_status()
    return resp.json()


def _send_linkedin_reply(reply: Reply, client: httpx.Client) -> dict:
    """Send reply to LinkedIn comment."""
    token = get_token("linkedin", "access_token") or ""
    person_urn = os.getenv("LINKEDIN_PERSON_URN", "")
    if not token or not person_urn:
        raise ValueError("Missing LinkedIn credentials")

    # Need the post URN — get it from the post
    from backend.db.models import Post
    session = get_session()
    post = session.query(Post).filter_by(id=reply.post_id).first()
    post_urn = post.platform_post_id if post else ""
    session.close()

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "X-Restli-Protocol-Version": "2.0.0"
    }
    payload = {
        "actor": person_urn,
        "message": {"text": reply.draft_reply}
    }

    resp = client.post(f"{LINKEDIN_BASE_URL}/socialActions/{post_urn}/comments",
                       headers=headers, json=payload)
    resp.raise_for_status()
    return resp.json() if resp.content else {"status": "ok"}

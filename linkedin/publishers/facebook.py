"""
Oybit — Facebook Publisher
Uses Facebook Graph API to publish posts to a Facebook Page.

Required ENV:
  FACEBOOK_PAGE_ACCESS_TOKEN — Page-level access token
  FACEBOOK_PAGE_ID           — Numeric page ID
"""

import os
import logging
import httpx

logger = logging.getLogger(__name__)

GRAPH_API = "https://graph.facebook.com/v21.0"


def _get_config():
    token = os.getenv("FACEBOOK_PAGE_ACCESS_TOKEN", "")
    page_id = os.getenv("FACEBOOK_PAGE_ID", "")

    if not token:
        raise ValueError("FACEBOOK_PAGE_ACCESS_TOKEN not set in environment.")
    if not page_id:
        raise ValueError("FACEBOOK_PAGE_ID not set in environment.")

    return token, page_id


async def publish_to_facebook(
    content_text: str,
    media_paths: list[str] | None = None,
    format_type: str = "text",
) -> dict:
    """Publish a post to a Facebook Page."""
    try:
        token, page_id = _get_config()

        if format_type == "text" or not media_paths:
            return await _publish_text(token, page_id, content_text)
        else:
            return await _publish_photo(token, page_id, content_text, media_paths[0])

    except ValueError as e:
        return {"success": False, "platform_post_id": None, "error": str(e)}
    except Exception as e:
        logger.error(f"Facebook publish failed: {e}")
        return {"success": False, "platform_post_id": None, "error": str(e)}


async def _publish_text(token: str, page_id: str, message: str) -> dict:
    """Publish a text-only post to the page feed."""
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            f"{GRAPH_API}/{page_id}/feed",
            params={
                "message": message,
                "access_token": token,
            },
        )

    if resp.status_code == 200:
        post_id = resp.json().get("id", "")
        return {"success": True, "platform_post_id": post_id, "error": None}
    else:
        return {"success": False, "platform_post_id": None, "error": f"HTTP {resp.status_code}: {resp.text[:300]}"}


async def _publish_photo(token: str, page_id: str, caption: str, image_path: str) -> dict:
    """Publish a photo post to the page."""
    async with httpx.AsyncClient(timeout=60) as client:
        with open(image_path, "rb") as f:
            resp = await client.post(
                f"{GRAPH_API}/{page_id}/photos",
                data={
                    "message": caption,
                    "access_token": token,
                },
                files={"source": (os.path.basename(image_path), f, "image/png")},
            )

    if resp.status_code == 200:
        post_id = resp.json().get("id", "")
        return {"success": True, "platform_post_id": post_id, "error": None}
    else:
        return {"success": False, "platform_post_id": None, "error": f"HTTP {resp.status_code}: {resp.text[:300]}"}

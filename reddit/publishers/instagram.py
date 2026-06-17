"""
Oybit — Instagram Publisher
Uses Instagram Graph API (via Facebook Business) to publish posts.

Required ENV:
  INSTAGRAM_ACCESS_TOKEN    — Long-lived page access token
  INSTAGRAM_USER_ID         — IG Business Account ID (numeric)
  INSTAGRAM_BASE_URL        — Public URL where media files are served (for IG to fetch)
"""

import os
import logging
import httpx
import asyncio

logger = logging.getLogger(__name__)

GRAPH_API = "https://graph.facebook.com/v21.0"


def _get_config():
    token = os.getenv("INSTAGRAM_ACCESS_TOKEN", "")
    user_id = os.getenv("INSTAGRAM_USER_ID", "")
    base_url = os.getenv("INSTAGRAM_BASE_URL", "")

    if not token:
        raise ValueError("INSTAGRAM_ACCESS_TOKEN not set in environment.")
    if not user_id:
        raise ValueError("INSTAGRAM_USER_ID not set in environment.")
    if not base_url:
        raise ValueError("INSTAGRAM_BASE_URL not set — IG needs publicly accessible image URLs.")

    return token, user_id, base_url


async def publish_to_instagram(
    account: str,
    content_text: str,
    media_paths: list[str] | None = None,
    format_type: str = "text",
) -> dict:
    """Publish to Instagram. IG requires at least one image — text-only is not supported."""
    try:
        token, user_id, base_url = _get_config()

        if not media_paths or len(media_paths) == 0:
            return {
                "success": False,
                "platform_post_id": None,
                "error": "Instagram requires at least one image. Text-only posts are not supported.",
            }

        if len(media_paths) == 1:
            return await _publish_single(token, user_id, base_url, content_text, media_paths[0])
        else:
            return await _publish_carousel(token, user_id, base_url, content_text, media_paths)

    except ValueError as e:
        return {"success": False, "platform_post_id": None, "error": str(e)}
    except Exception as e:
        logger.error(f"Instagram publish failed: {e}")
        return {"success": False, "platform_post_id": None, "error": str(e)}


async def _publish_single(
    token: str, user_id: str, base_url: str, caption: str, media_path: str
) -> dict:
    """Publish a single-image post."""
    image_url = f"{base_url.rstrip('/')}/{media_path.lstrip('/')}"

    async with httpx.AsyncClient(timeout=30) as client:
        # Step 1: Create media container
        resp = await client.post(
            f"{GRAPH_API}/{user_id}/media",
            params={
                "image_url": image_url,
                "caption": caption,
                "access_token": token,
            },
        )
        if resp.status_code != 200:
            return {"success": False, "platform_post_id": None, "error": f"Container creation failed: {resp.text[:300]}"}

        container_id = resp.json().get("id")

        # Step 2: Wait for container to be ready
        await asyncio.sleep(5)

        # Step 3: Publish
        resp = await client.post(
            f"{GRAPH_API}/{user_id}/media_publish",
            params={
                "creation_id": container_id,
                "access_token": token,
            },
        )

    if resp.status_code == 200:
        post_id = resp.json().get("id", "")
        return {"success": True, "platform_post_id": post_id, "error": None}
    else:
        return {"success": False, "platform_post_id": None, "error": f"Publish failed: {resp.text[:300]}"}


async def _publish_carousel(
    token: str, user_id: str, base_url: str, caption: str, media_paths: list[str]
) -> dict:
    """Publish a carousel post (multiple images)."""
    children_ids = []

    async with httpx.AsyncClient(timeout=30) as client:
        # Step 1: Create child containers for each image
        for path in media_paths:
            image_url = f"{base_url.rstrip('/')}/{path.lstrip('/')}"
            resp = await client.post(
                f"{GRAPH_API}/{user_id}/media",
                params={
                    "image_url": image_url,
                    "is_carousel_item": "true",
                    "access_token": token,
                },
            )
            if resp.status_code != 200:
                return {"success": False, "platform_post_id": None, "error": f"Carousel item failed: {resp.text[:300]}"}
            children_ids.append(resp.json()["id"])

        # Step 2: Wait for processing
        await asyncio.sleep(8)

        # Step 3: Create carousel container
        resp = await client.post(
            f"{GRAPH_API}/{user_id}/media",
            params={
                "caption": caption,
                "media_type": "CAROUSEL",
                "children": ",".join(children_ids),
                "access_token": token,
            },
        )
        if resp.status_code != 200:
            return {"success": False, "platform_post_id": None, "error": f"Carousel container failed: {resp.text[:300]}"}

        carousel_id = resp.json()["id"]

        # Step 4: Wait for carousel processing
        await asyncio.sleep(5)

        # Step 5: Publish
        resp = await client.post(
            f"{GRAPH_API}/{user_id}/media_publish",
            params={
                "creation_id": carousel_id,
                "access_token": token,
            },
        )

    if resp.status_code == 200:
        post_id = resp.json().get("id", "")
        return {"success": True, "platform_post_id": post_id, "error": None}
    else:
        return {"success": False, "platform_post_id": None, "error": f"Carousel publish failed: {resp.text[:300]}"}

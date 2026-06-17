"""
Oybit — LinkedIn Publisher
Uses LinkedIn API v2 to publish text, image, and carousel posts.

Required ENV:
  LINKEDIN_ACCESS_TOKEN — OAuth2 access token
  LINKEDIN_PERSON_URN   — e.g. "urn:li:person:XXXX" (your profile URN)
"""

import os
import logging
import httpx

logger = logging.getLogger(__name__)

API_BASE = "https://api.linkedin.com/v2"


def _get_headers():
    token = os.getenv("LINKEDIN_ACCESS_TOKEN", "")
    if not token:
        raise ValueError("LINKEDIN_ACCESS_TOKEN not set in environment.")
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "X-Restli-Protocol-Version": "2.0.0",
    }


def _get_person_urn():
    urn = os.getenv("LINKEDIN_PERSON_URN", "")
    if not urn:
        raise ValueError("LINKEDIN_PERSON_URN not set in environment.")
    return urn


async def publish_to_linkedin(
    content_text: str,
    media_paths: list[str] | None = None,
    format_type: str = "text",
) -> dict:
    """Publish a post to LinkedIn."""
    try:
        headers = _get_headers()
        person_urn = _get_person_urn()

        if format_type == "text" or not media_paths:
            return await _publish_text(headers, person_urn, content_text)
        elif format_type == "article" or format_type == "newsletter":
            # GAP 2.5 - LinkedIn Newsletter
            return await _publish_article(headers, person_urn, content_text)
        elif format_type == "image" or len(media_paths) == 1:
            return await _publish_image(headers, person_urn, content_text, media_paths[0])
        else:
            return await _publish_multi_image(headers, person_urn, content_text, media_paths)

    except ValueError as e:
        return {"success": False, "platform_post_id": None, "error": str(e)}
    except Exception as e:
        logger.error(f"LinkedIn publish failed: {e}")
        return {"success": False, "platform_post_id": None, "error": str(e)}


async def _publish_text(headers: dict, person_urn: str, text: str) -> dict:
    payload = {
        "author": person_urn,
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {"text": text},
                "shareMediaCategory": "NONE",
            }
        },
        "visibility": {
            "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
        },
    }

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(f"{API_BASE}/ugcPosts", headers=headers, json=payload)

    if resp.status_code in (200, 201):
        post_id = resp.headers.get("x-restli-id", resp.json().get("id", ""))
        return {"success": True, "platform_post_id": post_id, "error": None}
    else:
        return {"success": False, "platform_post_id": None, "error": f"HTTP {resp.status_code}: {resp.text[:300]}"}


async def _publish_article(headers: dict, person_urn: str, text: str) -> dict:
    """Publish a LinkedIn Article / Newsletter (GAP 2.5)."""
    # Note: LinkedIn API requires specific ARTICLE shareMediaCategory and originalUrl for articles.
    # We will format the text as a long-form post for now if newsletter API isn't fully provisioned.
    payload = {
        "author": person_urn,
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {"text": "A new article is out!"},
                "shareMediaCategory": "ARTICLE",
                "media": [
                    {
                        "status": "READY",
                        "description": {"text": text[:200]},
                        "originalUrl": "https://oybit.nyvora.com/newsletter",
                        "title": {"text": "Oybit Newsletter"}
                    }
                ]
            }
        },
        "visibility": {
            "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
        },
    }

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(f"{API_BASE}/ugcPosts", headers=headers, json=payload)

    if resp.status_code in (200, 201):
        post_id = resp.headers.get("x-restli-id", resp.json().get("id", ""))
        return {"success": True, "platform_post_id": post_id, "error": None}
    else:
        return {"success": False, "platform_post_id": None, "error": f"HTTP {resp.status_code}: {resp.text[:300]}"}


async def _register_image_upload(headers: dict, person_urn: str) -> tuple[str, str]:
    register_payload = {
        "registerUploadRequest": {
            "recipes": ["urn:li:digitalmediaRecipe:feedshare-image"],
            "owner": person_urn,
            "serviceRelationships": [
                {"relationshipType": "OWNER", "identifier": "urn:li:userGeneratedContent"}
            ],
        }
    }

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            f"{API_BASE}/assets?action=registerUpload",
            headers=headers,
            json=register_payload,
        )

    data = resp.json()
    upload_url = data["value"]["uploadMechanism"][
        "com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest"
    ]["uploadUrl"]
    asset_urn = data["value"]["asset"]
    return upload_url, asset_urn


async def _upload_image_bytes(upload_url: str, image_path: str, headers: dict) -> bool:
    with open(image_path, "rb") as f:
        image_bytes = f.read()

    upload_headers = {
        "Authorization": headers["Authorization"],
        "Content-Type": "application/octet-stream",
    }

    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.put(upload_url, headers=upload_headers, content=image_bytes)

    return resp.status_code in (200, 201)


async def _publish_image(headers: dict, person_urn: str, text: str, image_path: str) -> dict:
    upload_url, asset_urn = await _register_image_upload(headers, person_urn)
    uploaded = await _upload_image_bytes(upload_url, image_path, headers)

    if not uploaded:
        return {"success": False, "platform_post_id": None, "error": "Image upload to LinkedIn failed."}

    payload = {
        "author": person_urn,
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {"text": text},
                "shareMediaCategory": "IMAGE",
                "media": [{"status": "READY", "media": asset_urn}],
            }
        },
        "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"},
    }

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(f"{API_BASE}/ugcPosts", headers=headers, json=payload)

    if resp.status_code in (200, 201):
        post_id = resp.headers.get("x-restli-id", resp.json().get("id", ""))
        return {"success": True, "platform_post_id": post_id, "error": None}
    else:
        return {"success": False, "platform_post_id": None, "error": f"HTTP {resp.status_code}: {resp.text[:300]}"}


async def _publish_multi_image(headers: dict, person_urn: str, text: str, image_paths: list[str]) -> dict:
    media_items = []
    for path in image_paths:
        upload_url, asset_urn = await _register_image_upload(headers, person_urn)
        uploaded = await _upload_image_bytes(upload_url, path, headers)
        if not uploaded:
            return {"success": False, "platform_post_id": None, "error": f"Failed to upload image: {path}"}
        media_items.append({"status": "READY", "media": asset_urn})

    payload = {
        "author": person_urn,
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {"text": text},
                "shareMediaCategory": "IMAGE",
                "media": media_items,
            }
        },
        "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"},
    }

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(f"{API_BASE}/ugcPosts", headers=headers, json=payload)

    if resp.status_code in (200, 201):
        post_id = resp.headers.get("x-restli-id", resp.json().get("id", ""))
        return {"success": True, "platform_post_id": post_id, "error": None}
    else:
        return {"success": False, "platform_post_id": None, "error": f"HTTP {resp.status_code}: {resp.text[:300]}"}

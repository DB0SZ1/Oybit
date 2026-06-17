"""
Oybit — Instagram Personal Publisher
Publishes to Ahmad's personal Instagram via Meta Graph API v19.0.
Supports: single image, carousel, Reel (video), Story.
"""
import time
import logging
from typing import Optional

import httpx

from token_store.store import get_token

logger = logging.getLogger(__name__)

BASE_URL = "https://graph.facebook.com/v19.0"
MAX_RETRIES = 3
BACKOFF_SECONDS = [5, 15, 45]


class InstagramPersonalPublisher:
    """Publisher for Ahmad's personal Instagram account."""

    def __init__(self, dry_run: bool = False, http_client: httpx.Client = None):
        self.dry_run = dry_run
        self.client = http_client or httpx.Client(timeout=60)
        self.account_name = "instagram_personal"

    def _get_credentials(self) -> tuple[str, str]:
        """Get access token and user ID from token store or env."""
        import os
        token = get_token(self.account_name, "access_token") or os.getenv("INSTAGRAM_PERSONAL_ACCESS_TOKEN", "")
        user_id = os.getenv("INSTAGRAM_PERSONAL_USER_ID", "")
        if not token:
            raise ValueError("Missing INSTAGRAM_PERSONAL_ACCESS_TOKEN — cannot publish")
        if not user_id:
            raise ValueError("Missing INSTAGRAM_PERSONAL_USER_ID — cannot publish")
        return token, user_id

    def _api_call(self, method: str, url: str, **kwargs) -> dict:
        """Make API call with retry logic."""
        for attempt in range(MAX_RETRIES):
            try:
                if method == "GET":
                    resp = self.client.get(url, **kwargs)
                else:
                    resp = self.client.post(url, **kwargs)
                resp.raise_for_status()
                return resp.json()
            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error on attempt {attempt+1}: {e.response.status_code} {e.response.text}")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(BACKOFF_SECONDS[attempt])
                else:
                    raise
            except httpx.RequestError as e:
                logger.error(f"Request error on attempt {attempt+1}: {e}")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(BACKOFF_SECONDS[attempt])
                else:
                    raise

    def publish_single_image(self, image_url: str, caption: str) -> dict:
        """Publish a single image post."""
        token, user_id = self._get_credentials()

        # Step 1: Create media container
        container_payload = {
            "image_url": image_url,
            "caption": caption,
            "access_token": token
        }

        if self.dry_run:
            return {
                "dry_run": True,
                "type": "single_image",
                "payload": container_payload,
                "account": self.account_name
            }

        container = self._api_call("POST", f"{BASE_URL}/{user_id}/media", params=container_payload)
        container_id = container["id"]

        # Step 2: Publish
        publish_payload = {
            "creation_id": container_id,
            "access_token": token
        }
        result = self._api_call("POST", f"{BASE_URL}/{user_id}/media_publish", params=publish_payload)
        logger.info(f"Published single image to {self.account_name}: {result.get('id')}")
        return {"success": True, "post_id": result.get("id"), "account": self.account_name}

    def publish_carousel(self, image_urls: list[str], caption: str) -> dict:
        """Publish a carousel post (up to 10 slides)."""
        token, user_id = self._get_credentials()

        carousel_payload = {
            "type": "carousel",
            "items": [],
            "caption": caption,
            "access_token": token,
            "account": self.account_name
        }

        if self.dry_run:
            for url in image_urls:
                carousel_payload["items"].append({
                    "image_url": url,
                    "is_carousel_item": True
                })
            return {"dry_run": True, **carousel_payload}

        # Step 1: Create each item container
        child_ids = []
        for url in image_urls[:10]:
            item = self._api_call("POST", f"{BASE_URL}/{user_id}/media", params={
                "image_url": url,
                "is_carousel_item": "true",
                "access_token": token
            })
            child_ids.append(item["id"])

        # Step 2: Create carousel container
        carousel = self._api_call("POST", f"{BASE_URL}/{user_id}/media", params={
            "media_type": "CAROUSEL",
            "children": ",".join(child_ids),
            "caption": caption,
            "access_token": token
        })

        # Step 3: Publish
        result = self._api_call("POST", f"{BASE_URL}/{user_id}/media_publish", params={
            "creation_id": carousel["id"],
            "access_token": token
        })
        logger.info(f"Published carousel to {self.account_name}: {result.get('id')}")
        return {"success": True, "post_id": result.get("id"), "account": self.account_name}

    def _validate_video(self, video_url: str) -> None:
        """GAP 4.5: Instagram Video Pre-Upload Validation"""
        # In production, this would do a HEAD request or use ffprobe to check size/duration
        if not video_url.startswith("http"):
            raise ValueError(f"Video URL must be valid HTTP/HTTPS: {video_url}")
        if not video_url.endswith((".mp4", ".mov")):
            raise ValueError(f"Instagram requires .mp4 or .mov video format: {video_url}")

    def publish_reel(self, video_url: str, caption: str) -> dict:
        """Publish a Reel (video)."""
        self._validate_video(video_url)
        token, user_id = self._get_credentials()

        reel_payload = {
            "media_type": "REELS",
            "video_url": video_url,
            "caption": caption,
            "share_to_feed": "true",
            "access_token": token
        }

        if self.dry_run:
            return {"dry_run": True, "type": "reel", "payload": reel_payload, "account": self.account_name}

        container = self._api_call("POST", f"{BASE_URL}/{user_id}/media", params=reel_payload)
        container_id = container["id"]

        # Poll until VIDEO_READY
        for _ in range(30):
            status = self._api_call("GET", f"{BASE_URL}/{container_id}", params={
                "fields": "status_code",
                "access_token": token
            })
            if status.get("status_code") == "FINISHED":
                break
            time.sleep(5)

        result = self._api_call("POST", f"{BASE_URL}/{user_id}/media_publish", params={
            "creation_id": container_id,
            "access_token": token
        })
        logger.info(f"Published reel to {self.account_name}: {result.get('id')}")
        return {"success": True, "post_id": result.get("id"), "account": self.account_name}

    def publish_story(self, image_url: str) -> dict:
        """Publish a Story (photo)."""
        token, user_id = self._get_credentials()

        story_payload = {
            "image_url": image_url,
            "media_type": "STORIES",
            "access_token": token
        }

        if self.dry_run:
            return {"dry_run": True, "type": "story", "payload": story_payload, "account": self.account_name}

        container = self._api_call("POST", f"{BASE_URL}/{user_id}/media", params=story_payload)

        result = self._api_call("POST", f"{BASE_URL}/{user_id}/media_publish", params={
            "creation_id": container["id"],
            "access_token": token
        })
        logger.info(f"Published story to {self.account_name}: {result.get('id')}")
        return {"success": True, "post_id": result.get("id"), "account": self.account_name}

    def publish(self, post_data: dict) -> dict:
        """
        Unified publish method. Routes based on post format.
        post_data keys: format, content_text, media_urls, caption
        """
        fmt = post_data.get("format", "image")
        caption = post_data.get("content_text", "")
        media_urls = post_data.get("media_urls", [])

        if fmt == "carousel" and len(media_urls) > 1:
            return self.publish_carousel(media_urls, caption)
        elif fmt == "video" and media_urls:
            return self.publish_reel(media_urls[0], caption)
        elif fmt == "story" and media_urls:
            return self.publish_story(media_urls[0])
        elif media_urls:
            return self.publish_single_image(media_urls[0], caption)
        else:
            raise ValueError("Cannot publish to Instagram without media URLs")

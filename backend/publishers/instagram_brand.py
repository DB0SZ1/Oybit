"""
Oybit — Instagram Brand Publisher
Publishes to Nyvora brand Instagram via Meta Graph API v19.0.
Same flow as instagram_personal.py but uses brand tokens.
"""
import time
import logging
from typing import Optional

import httpx

from backend.token_store.store import get_token

logger = logging.getLogger(__name__)

BASE_URL = "https://graph.facebook.com/v19.0"
MAX_RETRIES = 3
BACKOFF_SECONDS = [5, 15, 45]


class InstagramBrandPublisher:
    """Publisher for Nyvora brand Instagram account."""

    def __init__(self, dry_run: bool = False, http_client: httpx.Client = None):
        self.dry_run = dry_run
        self.client = http_client or httpx.Client(timeout=60)
        self.account_name = "instagram_brand"

    def _get_credentials(self) -> tuple[str, str]:
        import os
        token = get_token(self.account_name, "access_token") or os.getenv("INSTAGRAM_BRAND_ACCESS_TOKEN", "")
        user_id = os.getenv("INSTAGRAM_BRAND_USER_ID", "")
        if not token:
            raise ValueError("Missing INSTAGRAM_BRAND_ACCESS_TOKEN — cannot publish")
        if not user_id:
            raise ValueError("Missing INSTAGRAM_BRAND_USER_ID — cannot publish")
        return token, user_id

    def _api_call(self, method: str, url: str, **kwargs) -> dict:
        for attempt in range(MAX_RETRIES):
            try:
                if method == "GET":
                    resp = self.client.get(url, **kwargs)
                else:
                    resp = self.client.post(url, **kwargs)
                resp.raise_for_status()
                return resp.json()
            except (httpx.HTTPStatusError, httpx.RequestError) as e:
                logger.error(f"API error attempt {attempt+1}: {e}")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(BACKOFF_SECONDS[attempt])
                else:
                    raise

    def publish_single_image(self, image_url: str, caption: str) -> dict:
        token, user_id = self._get_credentials()
        payload = {"image_url": image_url, "caption": caption, "access_token": token}
        if self.dry_run:
            return {"dry_run": True, "type": "single_image", "payload": payload, "account": self.account_name}
        container = self._api_call("POST", f"{BASE_URL}/{user_id}/media", params=payload)
        result = self._api_call("POST", f"{BASE_URL}/{user_id}/media_publish", params={
            "creation_id": container["id"], "access_token": token
        })
        return {"success": True, "post_id": result.get("id"), "account": self.account_name}

    def publish_carousel(self, image_urls: list[str], caption: str) -> dict:
        token, user_id = self._get_credentials()
        if self.dry_run:
            return {"dry_run": True, "type": "carousel", "items": [{"image_url": u} for u in image_urls],
                    "caption": caption, "access_token": token, "account": self.account_name}
        child_ids = []
        for url in image_urls[:10]:
            item = self._api_call("POST", f"{BASE_URL}/{user_id}/media", params={
                "image_url": url, "is_carousel_item": "true", "access_token": token
            })
            child_ids.append(item["id"])
        carousel = self._api_call("POST", f"{BASE_URL}/{user_id}/media", params={
            "media_type": "CAROUSEL", "children": ",".join(child_ids), "caption": caption, "access_token": token
        })
        result = self._api_call("POST", f"{BASE_URL}/{user_id}/media_publish", params={
            "creation_id": carousel["id"], "access_token": token
        })
        return {"success": True, "post_id": result.get("id"), "account": self.account_name}

    def publish_reel(self, video_url: str, caption: str) -> dict:
        token, user_id = self._get_credentials()
        payload = {"media_type": "REELS", "video_url": video_url, "caption": caption,
                   "share_to_feed": "true", "access_token": token}
        if self.dry_run:
            return {"dry_run": True, "type": "reel", "payload": payload, "account": self.account_name}
        container = self._api_call("POST", f"{BASE_URL}/{user_id}/media", params=payload)
        for _ in range(30):
            status = self._api_call("GET", f"{BASE_URL}/{container['id']}", params={
                "fields": "status_code", "access_token": token
            })
            if status.get("status_code") == "FINISHED":
                break
            time.sleep(5)
        result = self._api_call("POST", f"{BASE_URL}/{user_id}/media_publish", params={
            "creation_id": container["id"], "access_token": token
        })
        return {"success": True, "post_id": result.get("id"), "account": self.account_name}

    def publish_story(self, image_url: str) -> dict:
        token, user_id = self._get_credentials()
        payload = {"image_url": image_url, "media_type": "STORIES", "access_token": token}
        if self.dry_run:
            return {"dry_run": True, "type": "story", "payload": payload, "account": self.account_name}
        container = self._api_call("POST", f"{BASE_URL}/{user_id}/media", params=payload)
        result = self._api_call("POST", f"{BASE_URL}/{user_id}/media_publish", params={
            "creation_id": container["id"], "access_token": token
        })
        return {"success": True, "post_id": result.get("id"), "account": self.account_name}

    def publish(self, post_data: dict) -> dict:
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

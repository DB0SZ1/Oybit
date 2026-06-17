"""
Oybit — Pinterest Publisher (GAP 12.1)
Publishes pins to Pinterest using the Pinterest API v5.
"""
import httpx
import logging
import os

logger = logging.getLogger(__name__)

class PinterestPublisher:
    BASE_URL = "https://api.pinterest.com/v5"
    
    def __init__(self, dry_run: bool = False):
        self.access_token = os.getenv("PINTEREST_ACCESS_TOKEN", "")
        self.dry_run = dry_run
    
    def _headers(self):
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
    
    def publish(self, post_data: dict) -> dict:
        """Publish a pin to Pinterest."""
        if self.dry_run:
            return {"success": True, "dry_run": True, "platform": "pinterest"}
        
        board_id = post_data.get("board_id", os.getenv("PINTEREST_BOARD_ID", ""))
        if not board_id:
            return {"success": False, "error": "No board_id specified"}
        
        payload = {
            "board_id": board_id,
            "title": post_data.get("title", ""),
            "description": post_data.get("content_text", ""),
            "media_source": {
                "source_type": "image_url",
                "url": post_data.get("media_urls", [""])[0]
            }
        }
        
        # Add link if provided
        if post_data.get("link"):
            payload["link"] = post_data["link"]
        
        # Add alt text for SEO
        if post_data.get("alt_text"):
            payload["alt_text"] = post_data["alt_text"]
        
        try:
            resp = httpx.post(
                f"{self.BASE_URL}/pins",
                headers=self._headers(),
                json=payload,
                timeout=30
            )
            if resp.status_code == 201:
                data = resp.json()
                return {"success": True, "pin_id": data.get("id"), "platform": "pinterest"}
            else:
                return {"success": False, "error": f"HTTP {resp.status_code}: {resp.text[:200]}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def create_board(self, name: str, description: str = "") -> dict:
        """Create a Pinterest board."""
        if self.dry_run:
            return {"success": True, "dry_run": True}
        
        payload = {"name": name, "description": description, "privacy": "PUBLIC"}
        
        try:
            resp = httpx.post(f"{self.BASE_URL}/boards", headers=self._headers(), json=payload, timeout=15)
            if resp.status_code == 201:
                return {"success": True, "board_id": resp.json().get("id")}
            else:
                return {"success": False, "error": resp.text[:200]}
        except Exception as e:
            return {"success": False, "error": str(e)}

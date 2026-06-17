"""
Oybit — Facebook Groups Posting (GAP 7.3)
Posts to Facebook groups using the Graph API.
"""
import httpx
import logging
import os

logger = logging.getLogger(__name__)

class FacebookGroupPublisher:
    def __init__(self, dry_run: bool = False):
        self.access_token = os.getenv("FB_USER_TOKEN", "")
        self.dry_run = dry_run
    
    def post_to_group(self, group_id: str, message: str, link: str = None) -> dict:
        """Post to a Facebook group."""
        if self.dry_run:
            return {"success": True, "dry_run": True, "group_id": group_id}
        
        url = f"https://graph.facebook.com/v21.0/{group_id}/feed"
        payload = {"message": message, "access_token": self.access_token}
        if link:
            payload["link"] = link
        
        try:
            resp = httpx.post(url, data=payload, timeout=30)
            data = resp.json()
            if "id" in data:
                return {"success": True, "post_id": data["id"]}
            else:
                error = data.get("error", {}).get("message", "Unknown error")
                return {"success": False, "error": error}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def post_image_to_group(self, group_id: str, message: str, image_url: str) -> dict:
        """Post an image to a Facebook group."""
        if self.dry_run:
            return {"success": True, "dry_run": True}
        
        url = f"https://graph.facebook.com/v21.0/{group_id}/photos"
        payload = {"message": message, "url": image_url, "access_token": self.access_token}
        
        try:
            resp = httpx.post(url, data=payload, timeout=30)
            data = resp.json()
            if "id" in data:
                return {"success": True, "photo_id": data["id"]}
            else:
                return {"success": False, "error": data.get("error", {}).get("message", "Unknown")}
        except Exception as e:
            return {"success": False, "error": str(e)}

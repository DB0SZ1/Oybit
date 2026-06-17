"""
Oybit — Facebook Reels Publisher (GAPS_FINAL GAP 1.3)
"""
import httpx
import logging
import os
import time

logger = logging.getLogger(__name__)

class FacebookReelPublisher:
    def __init__(self, dry_run: bool = False):
        self.access_token = os.getenv("FB_PAGE_TOKEN", "")
        self.page_id = os.getenv("FB_PAGE_ID", "")
        self.dry_run = dry_run
    
    def publish(self, post_data: dict) -> dict:
        """Publish a reel to Facebook."""
        if self.dry_run:
            return {"success": True, "dry_run": True, "platform": "facebook_reel"}
        
        video_url = (post_data.get("media_urls") or [""])[0]
        description = post_data.get("content_text", "")
        
        if not video_url:
            return {"success": False, "error": "Reel requires a video URL"}
        
        # Step 1: Initialize upload
        init_url = f"https://graph.facebook.com/v21.0/{self.page_id}/video_reels"
        init_payload = {
            "upload_phase": "start",
            "access_token": self.access_token
        }
        
        try:
            resp = httpx.post(init_url, data=init_payload, timeout=30)
            data = resp.json()
            video_id = data.get("video_id")
            
            if not video_id:
                return {"success": False, "error": f"Init failed: {data}"}
            
            # Step 2: Upload video
            upload_url = f"https://rupload.facebook.com/video-upload/v21.0/{video_id}"
            headers = {
                "Authorization": f"OAuth {self.access_token}",
                "file_url": video_url
            }
            
            upload_resp = httpx.post(upload_url, headers=headers, timeout=120)
            if upload_resp.status_code != 200:
                return {"success": False, "error": f"Upload failed: {upload_resp.text[:200]}"}
            
            # Step 3: Publish
            publish_url = f"https://graph.facebook.com/v21.0/{self.page_id}/video_reels"
            publish_payload = {
                "upload_phase": "finish",
                "video_id": video_id,
                "description": description,
                "access_token": self.access_token
            }
            
            pub_resp = httpx.post(publish_url, data=publish_payload, timeout=30)
            pub_data = pub_resp.json()
            
            if pub_data.get("success"):
                return {"success": True, "video_id": video_id, "platform": "facebook_reel"}
            else:
                return {"success": False, "error": f"Publish failed: {pub_data}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

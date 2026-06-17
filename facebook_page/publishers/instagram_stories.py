"""
Oybit — Instagram Stories Publisher (GAPS_FINAL GAP 1.2)
Publishes stories via the Instagram Graph API.
"""
import httpx
import logging
import os

logger = logging.getLogger(__name__)

class InstagramStoryPublisher:
    def __init__(self, dry_run: bool = False):
        self.access_token = os.getenv("META_USER_TOKEN", "")
        self.ig_user_id = os.getenv("IG_USER_ID", "")
        self.dry_run = dry_run
    
    def publish(self, post_data: dict) -> dict:
        """Publish a story to Instagram."""
        if self.dry_run:
            return {"success": True, "dry_run": True, "platform": "instagram_story"}
        
        media_url = (post_data.get("media_urls") or [""])[0]
        if not media_url:
            return {"success": False, "error": "Story requires media (image or video)"}
        
        is_video = post_data.get("format") == "video" or media_url.endswith(('.mp4', '.mov'))
        
        # Step 1: Create story media container
        create_url = f"https://graph.facebook.com/v21.0/{self.ig_user_id}/media"
        
        if is_video:
            create_payload = {
                "media_type": "STORIES",
                "video_url": media_url,
                "access_token": self.access_token
            }
        else:
            create_payload = {
                "media_type": "STORIES",
                "image_url": media_url,
                "access_token": self.access_token
            }
        
        try:
            resp = httpx.post(create_url, data=create_payload, timeout=60)
            data = resp.json()
            
            if "id" not in data:
                error = data.get("error", {}).get("message", "Unknown error")
                return {"success": False, "error": f"Container creation failed: {error}"}
            
            container_id = data["id"]
            
            # Step 2: Publish the container
            publish_url = f"https://graph.facebook.com/v21.0/{self.ig_user_id}/media_publish"
            publish_payload = {
                "creation_id": container_id,
                "access_token": self.access_token
            }
            
            pub_resp = httpx.post(publish_url, data=publish_payload, timeout=30)
            pub_data = pub_resp.json()
            
            if "id" in pub_data:
                return {"success": True, "story_id": pub_data["id"], "platform": "instagram_story"}
            else:
                error = pub_data.get("error", {}).get("message", "Unknown")
                return {"success": False, "error": f"Publish failed: {error}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

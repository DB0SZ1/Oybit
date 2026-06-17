"""
Oybit — YouTube Publisher (GAP 12.2)
Uploads videos to YouTube using the YouTube Data API v3.
"""
import httpx
import logging
import os
import json

logger = logging.getLogger(__name__)

class YouTubePublisher:
    UPLOAD_URL = "https://www.googleapis.com/upload/youtube/v3/videos"
    METADATA_URL = "https://www.googleapis.com/youtube/v3/videos"
    
    def __init__(self, dry_run: bool = False):
        self.access_token = os.getenv("YOUTUBE_ACCESS_TOKEN", "")
        self.dry_run = dry_run
    
    def publish(self, post_data: dict) -> dict:
        """Upload a video to YouTube."""
        if self.dry_run:
            return {"success": True, "dry_run": True, "platform": "youtube"}
        
        video_path = post_data.get("video_path", "")
        if not video_path or not os.path.exists(video_path):
            return {"success": False, "error": f"Video file not found: {video_path}"}
        
        title = post_data.get("title", "Untitled")
        description = post_data.get("content_text", "")
        tags = post_data.get("tags", [])
        category_id = post_data.get("category_id", "22")  # 22 = People & Blogs
        privacy = post_data.get("privacy", "public")
        
        metadata = {
            "snippet": {
                "title": title,
                "description": description,
                "tags": tags,
                "categoryId": category_id
            },
            "status": {
                "privacyStatus": privacy,
                "selfDeclaredMadeForKids": False
            }
        }
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
        }
        
        try:
            # Step 1: Initiate resumable upload
            init_headers = {
                **headers,
                "Content-Type": "application/json; charset=UTF-8",
                "X-Upload-Content-Type": "video/*"
            }
            
            resp = httpx.post(
                f"{self.UPLOAD_URL}?uploadType=resumable&part=snippet,status",
                headers=init_headers,
                json=metadata,
                timeout=30
            )
            
            if resp.status_code != 200:
                return {"success": False, "error": f"Upload init failed: {resp.status_code} {resp.text[:200]}"}
            
            upload_url = resp.headers.get("Location")
            if not upload_url:
                return {"success": False, "error": "No upload URL returned"}
            
            # Step 2: Upload video file
            file_size = os.path.getsize(video_path)
            with open(video_path, 'rb') as f:
                upload_headers = {
                    **headers,
                    "Content-Type": "video/*",
                    "Content-Length": str(file_size)
                }
                upload_resp = httpx.put(upload_url, headers=upload_headers, content=f.read(), timeout=600)
            
            if upload_resp.status_code == 200:
                data = upload_resp.json()
                return {"success": True, "video_id": data.get("id"), "platform": "youtube"}
            else:
                return {"success": False, "error": f"Upload failed: {upload_resp.status_code}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

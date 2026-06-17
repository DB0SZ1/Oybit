"""
Oybit — LinkedIn Groups Posting (GAP 7.2)
Posts to LinkedIn groups using the UGC API.
"""
import httpx
import logging
import os

logger = logging.getLogger(__name__)

class LinkedInGroupPublisher:
    def __init__(self, dry_run: bool = False):
        self.access_token = os.getenv("LINKEDIN_ACCESS_TOKEN", "")
        self.dry_run = dry_run
    
    def post_to_group(self, group_id: str, text: str, author_urn: str = None) -> dict:
        """Post content to a LinkedIn group."""
        if not author_urn:
            author_urn = os.getenv("LINKEDIN_AUTHOR_URN", "")
        
        if self.dry_run:
            return {"success": True, "dry_run": True, "group_id": group_id}
        
        url = "https://api.linkedin.com/v2/ugcPosts"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "X-Restli-Protocol-Version": "2.0.0"
        }
        payload = {
            "author": author_urn,
            "containerEntity": f"urn:li:group:{group_id}",
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {"text": text},
                    "shareMediaCategory": "NONE"
                }
            },
            "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "CONTAINER"}
        }
        
        try:
            resp = httpx.post(url, headers=headers, json=payload, timeout=30)
            if resp.status_code == 201:
                return {"success": True, "post_id": resp.headers.get("x-restli-id")}
            else:
                return {"success": False, "error": f"HTTP {resp.status_code}: {resp.text[:200]}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

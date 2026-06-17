"""
Oybit — LinkedIn Newsletter (GAP 7.5)
Publishes long-form articles as LinkedIn newsletters.
"""
import httpx
import logging
import os

logger = logging.getLogger(__name__)

class LinkedInNewsletterPublisher:
    def __init__(self, dry_run: bool = False):
        self.access_token = os.getenv("LINKEDIN_ACCESS_TOKEN", "")
        self.author_urn = os.getenv("LINKEDIN_AUTHOR_URN", "")
        self.dry_run = dry_run
    
    def publish_article(self, title: str, body_html: str, 
                         thumbnail_url: str = None) -> dict:
        """
        Publish a LinkedIn article/newsletter edition.
        Uses the LinkedIn Articles API.
        """
        if self.dry_run:
            return {"success": True, "dry_run": True, "title": title}
        
        url = "https://api.linkedin.com/v2/articles"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "X-Restli-Protocol-Version": "2.0.0"
        }
        
        payload = {
            "author": self.author_urn,
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {"text": title},
                    "shareMediaCategory": "ARTICLE",
                    "media": [{
                        "status": "READY",
                        "originalUrl": thumbnail_url or "",
                        "title": {"text": title},
                        "description": {"text": body_html[:200]}
                    }]
                }
            },
            "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"}
        }
        
        try:
            resp = httpx.post(url, headers=headers, json=payload, timeout=30)
            if resp.status_code in (200, 201):
                return {"success": True, "article_id": resp.headers.get("x-restli-id")}
            else:
                return {"success": False, "error": f"HTTP {resp.status_code}: {resp.text[:200]}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

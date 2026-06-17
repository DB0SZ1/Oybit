"""
Oybit — LinkedIn Polls Publisher (GAPS_FINAL GAP 1.1)
"""
import httpx
import logging
import os

logger = logging.getLogger(__name__)

class LinkedInPollPublisher:
    def __init__(self, dry_run: bool = False):
        self.access_token = os.getenv("LINKEDIN_ACCESS_TOKEN", "")
        self.author_urn = os.getenv("LINKEDIN_AUTHOR_URN", "")
        self.dry_run = dry_run
    
    def publish(self, post_data: dict) -> dict:
        """Publish a poll to LinkedIn."""
        question = post_data.get("question", post_data.get("content_text", ""))
        options = post_data.get("poll_options", [])
        duration = post_data.get("poll_duration_days", 7)
        
        if len(options) < 2:
            return {"success": False, "error": "Poll requires at least 2 options"}
        if len(options) > 4:
            options = options[:4]  # LinkedIn max 4 options
        
        if self.dry_run:
            return {"success": True, "dry_run": True, "question": question, "options": options}
        
        from publishers.payload_builders import build_linkedin_poll_payload
        payload = build_linkedin_poll_payload(self.author_urn, question, options, duration)
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "X-Restli-Protocol-Version": "2.0.0"
        }
        
        try:
            resp = httpx.post("https://api.linkedin.com/v2/ugcPosts", headers=headers, json=payload, timeout=30)
            if resp.status_code in (200, 201):
                return {"success": True, "post_id": resp.headers.get("x-restli-id")}
            else:
                return {"success": False, "error": f"HTTP {resp.status_code}: {resp.text[:200]}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

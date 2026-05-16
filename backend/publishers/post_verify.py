"""
Oybit — Post-Publish Verification (GAP 5.2)
After publishing, verify the post actually exists on the platform.
"""
import httpx
import logging
import os
from datetime import datetime

logger = logging.getLogger(__name__)

def verify_meta_post(platform_post_id: str, access_token: str) -> dict:
    """Verify a post exists on Meta (Instagram/Facebook)."""
    url = f"https://graph.facebook.com/v21.0/{platform_post_id}"
    params = {"fields": "id,timestamp,permalink", "access_token": access_token}
    
    try:
        resp = httpx.get(url, params=params, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            return {"verified": True, "permalink": data.get("permalink"), "platform_id": data.get("id")}
        else:
            return {"verified": False, "error": f"HTTP {resp.status_code}: {resp.text[:200]}"}
    except Exception as e:
        return {"verified": False, "error": str(e)}

def verify_linkedin_post(post_urn: str, access_token: str) -> dict:
    """Verify a post exists on LinkedIn."""
    url = f"https://api.linkedin.com/v2/ugcPosts/{post_urn}"
    headers = {"Authorization": f"Bearer {access_token}"}
    
    try:
        resp = httpx.get(url, headers=headers, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            return {"verified": True, "lifecycle": data.get("lifecycleState")}
        else:
            return {"verified": False, "error": f"HTTP {resp.status_code}"}
    except Exception as e:
        return {"verified": False, "error": str(e)}

def verify_post(account: str, platform_post_id: str, access_token: str) -> dict:
    """Route verification to the correct platform handler."""
    if account in ("instagram_personal", "instagram_brand", "facebook"):
        return verify_meta_post(platform_post_id, access_token)
    elif account == "linkedin":
        return verify_linkedin_post(platform_post_id, access_token)
    else:
        return {"verified": None, "reason": f"No verifier for {account}"}

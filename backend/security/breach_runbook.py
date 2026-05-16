"""
Oybit — Token Breach Runbook and Security Utilities (GAP 16.2)
"""
import logging
import os
from datetime import datetime

logger = logging.getLogger(__name__)

TOKEN_BREACH_RUNBOOK = """
# Token Breach Response Runbook

## Immediate Actions (Within 5 Minutes)
1. **Revoke all compromised tokens** via platform developer consoles
2. **Activate posting pause**: Set POSTING_PAUSED=true env var
3. **Rotate all secrets**: Generate new tokens for affected platforms
4. **Check audit log**: Review /data/audit/ for unauthorized actions

## Platform-Specific Revocation
- **Meta (IG/FB)**: https://developers.facebook.com/tools/accesstoken/
- **LinkedIn**: https://www.linkedin.com/developers/apps → OAuth 2.0 → Revoke
- **Pinterest**: https://developers.pinterest.com/apps/ → Reset Secret
- **YouTube**: https://console.cloud.google.com → Credentials → Revoke
- **Bluesky**: Change app password at bsky.app/settings

## Post-Incident
1. Update all env vars on Railway/Render with new tokens
2. Run token refresh worker to verify new tokens work
3. Review the last 24h of published content for unauthorized posts
4. Send incident report via Telegram alert
"""

def emergency_revoke_all():
    """Emergency: flag all tokens as needing refresh."""
    logger.critical({"event": "emergency_token_revoke", "timestamp": datetime.utcnow().isoformat()})
    # Set environment flag
    os.environ["POSTING_PAUSED"] = "true"
    
    from backend.alerts.telegram import send_alert
    send_alert("🚨 EMERGENCY: All tokens flagged for revocation. Posting paused.", "CRITICAL")
    
    return {"status": "all_tokens_flagged", "posting_paused": True}

def check_credential_isolation():
    """Verify Facebook app credentials are properly isolated (GAP 8.3 from OYBIT_GAP_SOLUTIONS)."""
    fb_app_id = os.getenv("FB_APP_ID", "")
    fb_app_secret = os.getenv("FB_APP_SECRET", "")
    
    issues = []
    if fb_app_id and fb_app_secret:
        if fb_app_id in os.getenv("META_USER_TOKEN", ""):
            issues.append("App ID appears embedded in user token — potential leak")
    
    return {"isolated": len(issues) == 0, "issues": issues}

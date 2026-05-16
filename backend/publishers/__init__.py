"""
Oybit — Publisher Router
Dispatches content to the correct platform-specific publisher.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


async def publish(
    account: str,
    content_text: str,
    media_paths: list[str] | None = None,
    format_type: str = "text",
) -> dict:
    """
    Route a publish request to the correct platform publisher.
    Returns: { success: bool, platform_post_id: str, error: str }
    """
    if "linkedin" in account:
        from backend.publishers.linkedin import publish_to_linkedin
        return await publish_to_linkedin(content_text, media_paths, format_type)

    elif "instagram" in account:
        from backend.publishers.instagram import publish_to_instagram
        return await publish_to_instagram(account, content_text, media_paths, format_type)

    elif "facebook" in account:
        from backend.publishers.facebook import publish_to_facebook
        return await publish_to_facebook(content_text, media_paths, format_type)

    else:
        return {"success": False, "platform_post_id": None, "error": f"Unknown account type: {account}"}

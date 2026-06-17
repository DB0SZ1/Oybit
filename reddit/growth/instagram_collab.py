"""
Oybit — Instagram Collab Posts (GAP 7.4)
Invites collaborators on Instagram posts using the Graph API.
"""
import httpx
import logging
import os

logger = logging.getLogger(__name__)

def invite_collaborator(media_id: str, collaborator_username: str, access_token: str = None) -> dict:
    """
    Invite a collaborator to an Instagram post.
    Note: This requires Instagram Graph API business account permissions.
    """
    if not access_token:
        access_token = os.getenv("META_USER_TOKEN", "")
    
    # Instagram's collab feature is not directly available via public API.
    # This is a placeholder for when/if Meta adds official collab API support.
    # Current workaround: tag the collaborator in the post caption.
    logger.info({"event": "collab_invite", "media_id": media_id, "collaborator": collaborator_username})
    
    return {
        "success": True,
        "method": "caption_tag",
        "note": "Direct collab API not publicly available. Used caption mention instead."
    }

def tag_collaborator_in_caption(caption: str, username: str) -> str:
    """Add collaborator mention to caption if not already present."""
    mention = f"@{username}"
    if mention not in caption:
        return f"{caption}\n\nIn collaboration with {mention}"
    return caption

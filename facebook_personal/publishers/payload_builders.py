"""
Oybit — Post Type Enum & Payload Builders (GAP 5.1)
Ensures each platform gets the correct API payload structure.
"""
from enum import Enum

class PostType(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    CAROUSEL = "carousel"
    VIDEO = "video"
    REEL = "reel"
    STORY = "story"
    POLL = "poll"
    ARTICLE = "article"
    NEWSLETTER = "newsletter"

# Platform capability matrix
PLATFORM_CAPABILITIES = {
    "instagram_personal": [PostType.IMAGE, PostType.CAROUSEL, PostType.REEL, PostType.STORY],
    "instagram_brand": [PostType.IMAGE, PostType.CAROUSEL, PostType.REEL, PostType.STORY],
    "facebook": [PostType.TEXT, PostType.IMAGE, PostType.VIDEO, PostType.REEL],
    "linkedin": [PostType.TEXT, PostType.IMAGE, PostType.CAROUSEL, PostType.ARTICLE, PostType.POLL, PostType.NEWSLETTER],
    "reddit": [PostType.TEXT, PostType.IMAGE],
    "pinterest": [PostType.IMAGE, PostType.VIDEO],
    "youtube": [PostType.VIDEO],
    "bluesky": [PostType.TEXT, PostType.IMAGE],
}

def validate_post_type(account: str, post_type: str) -> bool:
    """Check if the post type is supported by the account's platform."""
    caps = PLATFORM_CAPABILITIES.get(account, [])
    return PostType(post_type) in caps

def build_meta_image_payload(page_id: str, image_url: str, caption: str) -> dict:
    """Build Meta Graph API payload for image post."""
    return {
        "url": image_url,
        "caption": caption,
        "access_token": "{{TOKEN}}"  # Replaced at publish time
    }

def build_meta_carousel_payload(page_id: str, media_ids: list[str], caption: str) -> dict:
    """Build Meta Graph API carousel payload (two-step process)."""
    return {
        "media_type": "CAROUSEL",
        "children": media_ids,
        "caption": caption,
        "access_token": "{{TOKEN}}"
    }

def build_linkedin_image_payload(author_urn: str, text: str, image_urn: str) -> dict:
    """Build LinkedIn UGC Post payload for image."""
    return {
        "author": author_urn,
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {"text": text},
                "shareMediaCategory": "IMAGE",
                "media": [{
                    "status": "READY",
                    "media": image_urn
                }]
            }
        },
        "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"}
    }

def build_linkedin_poll_payload(author_urn: str, question: str, options: list[str], duration_days: int = 7) -> dict:
    """Build LinkedIn poll payload."""
    return {
        "author": author_urn,
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {"text": question},
                "shareMediaCategory": "NONE",
                "poll": {
                    "question": question,
                    "options": [{"text": opt} for opt in options[:4]],
                    "settings": {"duration": f"P{duration_days}D"}
                }
            }
        },
        "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"}
    }

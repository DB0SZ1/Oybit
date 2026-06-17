"""
Oybit — Bluesky Rich Text Facets (GAP 12.3)
Properly encodes mentions (@), links, and hashtags as Bluesky facets.
"""
import re
import logging

logger = logging.getLogger(__name__)

def build_facets(text: str) -> list[dict]:
    """
    Parse text and generate Bluesky-compatible facets for:
    - Mentions (@handle.bsky.social)
    - URLs (https://...)
    - Hashtags (#tag)
    
    Bluesky requires byte offsets, not character offsets.
    """
    facets = []
    text_bytes = text.encode('utf-8')
    
    # Mentions: @handle.bsky.social
    for match in re.finditer(r'@([\w.-]+\.[\w.-]+)', text):
        handle = match.group(1)
        start_char = match.start()
        end_char = match.end()
        
        # Convert char offset to byte offset
        byte_start = len(text[:start_char].encode('utf-8'))
        byte_end = len(text[:end_char].encode('utf-8'))
        
        facets.append({
            "index": {"byteStart": byte_start, "byteEnd": byte_end},
            "features": [{
                "$type": "app.bsky.richtext.facet#mention",
                "did": ""  # Resolved at publish time via API
            }]
        })
    
    # URLs
    for match in re.finditer(r'https?://\S+', text):
        url = match.group(0)
        byte_start = len(text[:match.start()].encode('utf-8'))
        byte_end = len(text[:match.end()].encode('utf-8'))
        
        facets.append({
            "index": {"byteStart": byte_start, "byteEnd": byte_end},
            "features": [{
                "$type": "app.bsky.richtext.facet#link",
                "uri": url
            }]
        })
    
    # Hashtags
    for match in re.finditer(r'#(\w+)', text):
        tag = match.group(1)
        byte_start = len(text[:match.start()].encode('utf-8'))
        byte_end = len(text[:match.end()].encode('utf-8'))
        
        facets.append({
            "index": {"byteStart": byte_start, "byteEnd": byte_end},
            "features": [{
                "$type": "app.bsky.richtext.facet#tag",
                "tag": tag
            }]
        })
    
    return facets

def build_bluesky_post(text: str, reply_to: dict = None) -> dict:
    """Build a complete Bluesky post record with facets."""
    from datetime import datetime
    
    record = {
        "$type": "app.bsky.feed.post",
        "text": text,
        "createdAt": datetime.utcnow().isoformat() + "Z",
    }
    
    facets = build_facets(text)
    if facets:
        record["facets"] = facets
    
    if reply_to:
        record["reply"] = reply_to
    
    return record

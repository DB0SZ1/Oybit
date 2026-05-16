"""
Oybit — Content Repurposer
Takes blog post content or vlog transcript → calls OpenRouter
→ returns dict of platform-native slices.
"""
import os
import logging

import httpx

from backend.content.generator import call_openrouter

logger = logging.getLogger(__name__)


def repurpose(content: str, content_type: str = "blog",
              http_client: httpx.Client = None) -> dict:
    """
    Repurpose a blog post or vlog transcript into platform-native slices.

    Args:
        content: full blog post text or vlog transcript
        content_type: "blog" or "vlog"
        http_client: injectable HTTP client

    Returns:
        dict with keys: linkedin, instagram_personal, instagram_brand, facebook
    """
    system_prompt = (
        "You are a content repurposing expert. You take long-form content and "
        "create platform-native social media posts. Each platform version must feel "
        "native to that platform — not just a copy-paste with different lengths. "
        "Write in Ahmad's voice: direct, technical, real, with proof and consequences. "
        "Never be generic. Every post must contain at least one of: system insight, "
        "real consequence, technical mechanism, or contradiction."
    )

    user_prompt = f"""Repurpose this {content_type} into 4 platform-native posts.

SOURCE CONTENT:
{content}

Generate exactly 4 versions with these headers (include the header):

LINKEDIN:
[Write a professional post, under 1300 chars. Extract the key insight or lesson. 
Use thought leadership register. No hashtag spam. End with a question or reflection.]

INSTAGRAM_PERSONAL:
[Write a casual, hook-first Instagram caption. Personal, relatable, build-in-public tone. 
Ahmad's personal voice. Start with a strong hook that stops scrolling.]

INSTAGRAM_BRAND:
[Write a brand-focused version for Nyvora. Professional but not corporate. 
Product/brand angle if relevant. Clean, polished.]

FACEBOOK:
[Write a longer-form community post. Discussion-oriented. 
End with a question that invites comments.]

Return ONLY the 4 posts with their headers. No extra commentary."""

    api_key = os.getenv("OPENROUTER_API_KEY", "")
    if not api_key:
        raise ValueError("Missing OPENROUTER_API_KEY")

    model = os.getenv("OPENROUTER_DEFAULT_MODEL", "meta-llama/llama-4-scout")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "HTTP-Referer": "https://oybit.nyvora.com",
        "X-Title": "Oybit",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 3000
    }

    client = http_client or httpx.Client(timeout=120)
    response = client.post("https://openrouter.ai/api/v1/chat/completions",
                           headers=headers, json=payload)
    response.raise_for_status()

    data = response.json()
    raw_content = data["choices"][0]["message"]["content"]

    # Parse the 4 platform versions
    result = _parse_platform_slices(raw_content)
    return result


def _parse_platform_slices(content: str) -> dict:
    """Parse platform-specific content from OpenRouter response."""
    result = {
        "linkedin": "",
        "instagram_personal": "",
        "instagram_brand": "",
        "facebook": ""
    }

    sections = {
        "LINKEDIN:": "linkedin",
        "INSTAGRAM_PERSONAL:": "instagram_personal",
        "INSTAGRAM_BRAND:": "instagram_brand",
        "FACEBOOK:": "facebook"
    }

    # Find each section
    for header, key in sections.items():
        start_idx = content.upper().find(header.upper())
        if start_idx == -1:
            # Try alternative headers
            alt_headers = {
                "linkedin": ["LINKEDIN", "LinkedIn:"],
                "instagram_personal": ["INSTAGRAM PERSONAL:", "IG PERSONAL:"],
                "instagram_brand": ["INSTAGRAM BRAND:", "IG BRAND:"],
                "facebook": ["FACEBOOK", "FB:"]
            }
            for alt in alt_headers.get(key, []):
                start_idx = content.upper().find(alt.upper())
                if start_idx != -1:
                    break

        if start_idx == -1:
            continue

        # Find the content between this header and the next
        content_start = content.find("\n", start_idx)
        if content_start == -1:
            continue

        # Find next section header
        next_starts = []
        for other_header in sections.keys():
            if other_header != header:
                idx = content.upper().find(other_header.upper(), content_start)
                if idx != -1:
                    next_starts.append(idx)

        if next_starts:
            content_end = min(next_starts)
        else:
            content_end = len(content)

        text = content[content_start:content_end].strip()
        # Clean up
        text = text.strip("-").strip()
        result[key] = text

    return result

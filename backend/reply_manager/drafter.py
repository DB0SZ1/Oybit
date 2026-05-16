"""
Oybit — Reply Drafter
AI reply drafts using persona voice via OpenRouter.
"""
import os
import logging

import httpx

from backend.db.models import Reply, get_session

logger = logging.getLogger(__name__)


def draft_reply(reply_id: int, engine=None, http_client: httpx.Client = None) -> str:
    """
    Generate an AI draft reply for a comment using Ahmad's voice.

    Args:
        reply_id: ID of the Reply record
        engine: DB engine
        http_client: injectable HTTP client

    Returns:
        Draft reply text
    """
    session = get_session(engine)
    try:
        reply = session.query(Reply).filter_by(id=reply_id).first()
        if not reply:
            raise ValueError(f"Reply {reply_id} not found")

        # Platform tone adjustment
        tone = _get_platform_tone(reply.account)

        system_prompt = (
            f"You are Ahmad, replying to a comment on your {reply.account} post. "
            f"Tone: {tone}. "
            f"Reply naturally, like a real person. Be direct, warm, and real. "
            f"Keep it concise (1-3 sentences max). "
            f"Never use corporate language. Never start with 'Thank you for your comment.' "
            f"Match the energy of the comment — if they're excited, be excited back. "
            f"If they ask a question, answer it directly with proof or a real example."
        )

        user_prompt = (
            f"Comment type: {reply.comment_type}\n"
            f"Comment: \"{reply.comment_text}\"\n\n"
            f"Write a natural reply as Ahmad."
        )

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
            "max_tokens": 200
        }

        client = http_client or httpx.Client(timeout=60)
        response = client.post("https://openrouter.ai/api/v1/chat/completions",
                               headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        draft = data["choices"][0]["message"]["content"].strip()

        # Clean up
        draft = draft.strip('"').strip("'")

        # Update Reply record
        reply.draft_reply = draft
        reply.status = "draft_ready"
        session.commit()

        logger.info(f"Drafted reply for comment {reply_id}: {draft[:50]}...")
        return draft

    finally:
        session.close()


def _get_platform_tone(account: str) -> str:
    """Get tone guidance per platform."""
    tones = {
        "instagram_personal": "casual, warm, emoji-friendly, personal, relatable",
        "instagram_brand": "professional but approachable, Nyvora voice, helpful",
        "facebook": "friendly, community-oriented, conversational, inclusive",
        "linkedin": "thoughtful, considered, professional, value-adding, substantive"
    }
    return tones.get(account, "friendly, direct, authentic")

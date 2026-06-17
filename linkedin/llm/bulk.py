"""
Oybit — Bulk Content Generator
Batches generation calls → returns full week/month content plan.
"""
import os
import logging
from typing import Optional
from datetime import datetime, timedelta

from llm.generator import call_openrouter

logger = logging.getLogger(__name__)


def generate_bulk(topic_briefs: list[dict], http_client=None) -> list[dict]:
    """
    Generate content for multiple topic briefs in batch.

    Args:
        topic_briefs: list of dicts with:
            - topic: str
            - platform: str
            - account: str
            - format_type: str (optional)

    Returns:
        list of dicts with: topic, platform, account, variants (list of strings)
    """
    results = []

    for brief in topic_briefs:
        topic = brief.get("topic", "")
        platform = brief.get("platform", "linkedin")
        account = brief.get("account", "linkedin")

        system_prompt = (
            f"You are Ahmad, a technical content creator. "
            f"Generate content for {platform}. "
            f"Every post must contain at least one of: system insight, "
            f"real consequence, technical mechanism, or contradiction. "
            f"Write in first person, direct, with proof."
        )

        user_prompt = f"Create a post about: {topic}"

        try:
            variants = call_openrouter(
                system_prompt, user_prompt,
                num_variants=5,
                http_client=http_client
            )
            results.append({
                "topic": topic,
                "platform": platform,
                "account": account,
                "variants": variants,
                "generated_at": datetime.utcnow().isoformat()
            })
            logger.info(f"Bulk generated {len(variants)} variants for: {topic[:50]}")
        except Exception as e:
            logger.error(f"Failed to generate for topic '{topic[:50]}': {e}")
            results.append({
                "topic": topic,
                "platform": platform,
                "account": account,
                "variants": [],
                "error": str(e)
            })

    return results


def generate_weekly_plan(topics: list[str], accounts: list[str] = None) -> list[dict]:
    """
    Generate a full week of content across accounts.

    Args:
        topics: list of topic strings (at least 7)
        accounts: list of account names to distribute across

    Returns:
        list of dicts with date, account, topic, variants
    """
    if accounts is None:
        accounts = ["linkedin", "instagram_personal", "instagram_brand", "facebook"]

    briefs = []
    today = datetime.utcnow()

    for i, topic in enumerate(topics[:28]):
        account = accounts[i % len(accounts)]
        scheduled_date = today + timedelta(days=i // len(accounts))

        briefs.append({
            "topic": topic,
            "platform": account,
            "account": account,
            "scheduled_date": scheduled_date.isoformat()
        })

    results = generate_bulk(briefs)

    # Add scheduling info
    for i, result in enumerate(results):
        if i < len(briefs):
            result["scheduled_date"] = briefs[i].get("scheduled_date")

    return results

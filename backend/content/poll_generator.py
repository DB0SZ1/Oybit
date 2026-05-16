"""
Poll Content Generator — Generates LinkedIn poll questions + options from topic briefs.
Enforces LinkedIn poll constraints: question ≤140 chars, 2-4 options, each ≤30 chars.
"""

import json
from backend.content.generator import call_openrouter_raw
from backend.logger import get_logger

logger = get_logger("content.poll_generator")

# LinkedIn poll constraints
MAX_QUESTION_LENGTH = 140
MAX_OPTION_LENGTH = 30
MIN_OPTIONS = 2
MAX_OPTIONS = 4


def generate_linkedin_poll(
    topic_brief: str,
    persona_context: str = "",
    audience: str = "Nigerian tech professionals, developers, founders",
) -> dict:
    """
    Generate a LinkedIn poll from a topic brief.

    Args:
        topic_brief: the narrative/topic to build a poll around
        persona_context: Ahmad's persona context for voice alignment
        audience: target audience description

    Returns:
        dict with question, options, duration_days, and commentary
    """
    prompt = (
        f"Generate a LinkedIn poll for this topic:\n"
        f'"{topic_brief[:300]}"\n\n'
        f"Target audience: {audience}\n"
        f"Voice: Conversational, direct, no fluff. Ahmad's style — builder who ships.\n"
        f"{f'Persona context: {persona_context[:200]}' if persona_context else ''}\n\n"
        f"CONSTRAINTS:\n"
        f"- Question: max {MAX_QUESTION_LENGTH} characters\n"
        f"- Options: exactly 4, each max {MAX_OPTION_LENGTH} characters\n"
        f"- Include a commentary text (1-2 sentences) that Ahmad posts as a comment after the poll\n"
        f"- Duration: 3 or 7 days\n\n"
        f"Return ONLY valid JSON:\n"
        f'{{"question": "...", "options": ["A", "B", "C", "D"], "duration_days": 7, "commentary": "..."}}'
    )

    try:
        result = call_openrouter_raw(prompt, max_tokens=300)
        cleaned = result.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[1]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]

        data = json.loads(cleaned)
        poll = _validate_and_fix_poll(data)
        logger.info("Poll generated", extra={"question": poll["question"][:50]})
        return poll

    except Exception as e:
        logger.error("Poll generation failed", extra={"error": str(e)})
        raise


def _validate_and_fix_poll(data: dict) -> dict:
    """Validate and fix poll to meet LinkedIn constraints."""
    question = data.get("question", "")[:MAX_QUESTION_LENGTH]
    options = data.get("options", [])

    # Ensure 2-4 options
    options = [str(opt)[:MAX_OPTION_LENGTH] for opt in options[:MAX_OPTIONS]]
    while len(options) < MIN_OPTIONS:
        options.append("Other")

    return {
        "question": question,
        "options": options,
        "duration_days": data.get("duration_days", 7),
        "commentary": data.get("commentary", ""),
        "post_type": "poll",
        "platform": "linkedin",
    }


def generate_poll_from_analytics(
    top_performing_topics: list,
    audience_interests: list = None,
) -> dict:
    """
    Generate a poll based on analytics data — what topics are performing well,
    and what the audience seems interested in.
    """
    topics_str = ", ".join(top_performing_topics[:5])
    prompt = (
        f"Based on these top-performing content topics: {topics_str}\n"
        f"Generate a LinkedIn poll that would engage this audience by asking "
        f"them about their preferences or experiences with these topics.\n\n"
        f"CONSTRAINTS: question ≤{MAX_QUESTION_LENGTH} chars, 4 options each ≤{MAX_OPTION_LENGTH} chars.\n"
        f"Return ONLY valid JSON: {{\"question\": \"...\", \"options\": [...], \"duration_days\": 7, \"commentary\": \"...\"}}"
    )

    try:
        result = call_openrouter_raw(prompt, max_tokens=250)
        cleaned = result.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[1]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
        data = json.loads(cleaned)
        return _validate_and_fix_poll(data)
    except Exception as e:
        logger.error("Analytics-based poll generation failed", extra={"error": str(e)})
        raise

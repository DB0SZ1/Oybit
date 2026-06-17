"""
Instagram Stories Content Generator — Generates Story-format content.
Stories are conversion tools (lurker → follower), not reach tools.
Each Story should give a reason to follow NOW.
"""

import json
from llm.generator import call_openrouter_raw
from logger import get_logger

logger = get_logger("content.stories_generator")

# IG Story constraints
MAX_CAPTION_VISIBLE = 125  # chars visible before "more"
MAX_HASHTAGS = 5  # Stories don't benefit from many hashtags

STORY_TYPES = [
    "behind_the_scenes",   # Show the work in progress
    "poll_question",       # Interactive poll
    "quiz",                # Knowledge quiz
    "ama_prompt",          # "Ask me anything" prompt
    "quick_tip",           # 1 quick actionable tip
    "milestone",           # Celebrating a win/milestone
    "teaser",              # Teaser for upcoming content
    "day_in_life",         # "Building X today" narrative
]


def generate_story_content(
    topic_brief: str,
    story_type: str = None,
    account: str = "instagram_personal",
    persona_context: str = "",
) -> dict:
    """
    Generate Instagram Story content.

    Args:
        topic_brief: the narrative/topic for the story
        story_type: type of story (auto-selected if None)
        account: instagram_personal or instagram_brand
        persona_context: Ahmad's persona for voice alignment

    Returns:
        dict with story_type, text_overlay, caption, sticker_type, cta, visual_description
    """
    if story_type is None:
        story_type = "behind_the_scenes"  # Default to most authentic type

    prompt = (
        f"Generate an Instagram Story for this topic:\n"
        f'"{topic_brief[:300]}"\n\n'
        f"Story type: {story_type}\n"
        f"Account: {account}\n"
        f"Voice: {'Casual, raw, personal — like texting a friend' if account == 'instagram_personal' else 'Professional but approachable — brand perspective'}\n"
        f"{f'Persona: {persona_context[:200]}' if persona_context else ''}\n\n"
        f"CONSTRAINTS:\n"
        f"- Text overlay: max 3 lines, 40 chars per line (visible on screen)\n"
        f"- Caption (if any): max {MAX_CAPTION_VISIBLE} chars\n"
        f"- Stories are raw and casual, NOT polished feed content\n"
        f"- Must give viewer a reason to follow or engage NOW\n\n"
        f"Return ONLY valid JSON:\n"
        f'{{"story_type": "{story_type}", '
        f'"text_overlay": ["line1", "line2"], '
        f'"caption": "optional short caption", '
        f'"sticker_type": "poll|quiz|question|countdown|none", '
        f'"sticker_content": {{"question": "...", "options": ["A", "B"]}}, '
        f'"cta": "what you want viewer to do", '
        f'"visual_description": "what the background should look like", '
        f'"background_color": "#hex"}}'
    )

    try:
        result = call_openrouter_raw(prompt, max_tokens=350)
        cleaned = result.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[1]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]

        data = json.loads(cleaned)
        story = _validate_story(data)
        logger.info("Story content generated", extra={"type": story["story_type"]})
        return story

    except Exception as e:
        logger.error("Story generation failed", extra={"error": str(e)})
        raise


def _validate_story(data: dict) -> dict:
    """Validate and clean story content."""
    text_overlay = data.get("text_overlay", [])
    # Enforce line length limits
    text_overlay = [str(line)[:40] for line in text_overlay[:3]]

    caption = str(data.get("caption", ""))[:MAX_CAPTION_VISIBLE]

    return {
        "story_type": data.get("story_type", "behind_the_scenes"),
        "text_overlay": text_overlay,
        "caption": caption,
        "sticker_type": data.get("sticker_type", "none"),
        "sticker_content": data.get("sticker_content", {}),
        "cta": data.get("cta", ""),
        "visual_description": data.get("visual_description", ""),
        "background_color": data.get("background_color", "#1a1a2e"),
        "post_type": "story",
        "platform": "instagram",
    }


def generate_story_series(
    topic_brief: str,
    count: int = 3,
    account: str = "instagram_personal",
) -> list:
    """
    Generate a sequence of connected Stories for a narrative arc.
    E.g., teaser → behind_the_scenes → cta
    """
    series_types = ["teaser", "behind_the_scenes", "quick_tip"][:count]
    stories = []

    for stype in series_types:
        story = generate_story_content(
            topic_brief=topic_brief,
            story_type=stype,
            account=account,
        )
        stories.append(story)

    return stories

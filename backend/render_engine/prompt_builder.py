"""
Oybit — Image Prompt Builder
Reads persona.md visual identity → builds detailed image generation prompt.
Separate from Agent A's text prompt builder.
"""
import os
import logging
import re

logger = logging.getLogger(__name__)

# Default visual identity for when persona.md isn't available
DEFAULT_VISUAL_IDENTITY = {
    "primary_color": "#1a1a2e",
    "secondary_color": "#16213e",
    "accent_color": "#e94560",
    "style": "modern, clean, tech-forward",
    "mood": "professional, innovative, dynamic",
    "aesthetic": "Linear/Vercel/Notion minimal aesthetic"
}

PLATFORM_ASPECT_RATIOS = {
    "instagram_personal": "1:1 square format (1080x1080)",
    "instagram_brand": "1:1 square format (1080x1080)",
    "instagram_reel": "9:16 vertical format (1080x1920)",
    "linkedin": "1.91:1 landscape format (1200x628)",
    "facebook": "16:9 landscape format (1280x720)"
}

QUALITY_MARKERS = [
    "high resolution", "sharp focus", "professional quality",
    "clean composition", "vibrant", "detailed"
]


def _read_persona_visual_identity(persona_path: str = None) -> dict:
    """Extract visual identity from persona.md if available."""
    if persona_path is None:
        persona_path = os.path.join(
            os.getenv("PERSONA_DATA_DIR",
                       os.path.join(os.path.dirname(__file__), "..", "..", "data", "personas", "ahmad")),
            "persona.md"
        )

    identity = DEFAULT_VISUAL_IDENTITY.copy()

    try:
        if os.path.exists(persona_path):
            with open(persona_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Extract colors if found
            color_match = re.findall(r'#[0-9a-fA-F]{6}', content)
            if len(color_match) >= 1:
                identity["primary_color"] = color_match[0]
            if len(color_match) >= 2:
                identity["secondary_color"] = color_match[1]
            if len(color_match) >= 3:
                identity["accent_color"] = color_match[2]

            # Extract hard stops to avoid in visual prompts
            hard_stops = []
            in_hard_stops = False
            for line in content.split("\n"):
                if "hard stop" in line.lower() or "hard_stop" in line.lower():
                    in_hard_stops = True
                    continue
                if in_hard_stops and line.startswith("- "):
                    hard_stops.append(line.strip("- ").strip())
                elif in_hard_stops and line.startswith("#"):
                    break
            identity["hard_stops"] = hard_stops
    except Exception as e:
        logger.warning(f"Could not read persona visual identity: {e}")

    return identity


def build_image_prompt(post_brief: str, platform: str = "instagram_personal",
                       account_type: str = "personal", aspect_ratio: str = None,
                       persona_path: str = None) -> str:
    """
    Build a detailed image generation prompt for Pollinations.ai.

    Args:
        post_brief: topic/content brief for the post
        platform: target platform (instagram_personal, instagram_brand, linkedin, facebook)
        account_type: personal or brand
        aspect_ratio: override aspect ratio guidance
        persona_path: path to persona.md

    Returns:
        Detailed 150–200 word image generation prompt
    """
    identity = _read_persona_visual_identity(persona_path)

    # Platform-specific aspect ratio
    ar_guidance = aspect_ratio or PLATFORM_ASPECT_RATIOS.get(platform, "1:1 square format")

    # Style modifiers based on account type
    if account_type == "brand" or platform == "instagram_brand":
        style_modifier = (
            "Clean, minimal, professional design with brand identity. "
            "Product-forward aesthetic, corporate but approachable. "
            "Nyvora brand colors and visual language."
        )
    elif platform == "linkedin":
        style_modifier = (
            "Professional, thought leadership aesthetic. "
            "Minimal design, muted tones with selective accent color. "
            "Business-appropriate, clean typography emphasis."
        )
    elif platform == "facebook":
        style_modifier = (
            "Engaging, community-oriented visual. Dynamic composition. "
            "Bold colors, clear subject, conversation-starting imagery."
        )
    else:
        style_modifier = (
            "Authentic, build-in-public aesthetic. Modern developer culture. "
            "Dark mode feel, coding vibes, startup energy. "
            "Raw but polished, showing real work."
        )

    # Build the prompt
    quality = ", ".join(QUALITY_MARKERS[:4])

    prompt = (
        f"Create a {ar_guidance} image for a social media post about: {post_brief}. "
        f"{style_modifier} "
        f"Color palette: primary {identity['primary_color']}, "
        f"secondary {identity['secondary_color']}, "
        f"accent {identity['accent_color']}. "
        f"Style: {identity['style']}. "
        f"Mood: {identity['mood']}. "
        f"{identity['aesthetic']}. "
        f"{quality}. "
        f"No text overlays, no watermarks, no logos. "
        f"Abstract or symbolic representation, not literal. "
        f"Suitable for tech and startup audience."
    )

    # Remove any hard stop topics from prompt
    hard_stops = identity.get("hard_stops", [])
    for stop in hard_stops:
        prompt = prompt.replace(stop, "")

    # Remove markdown formatting
    prompt = prompt.replace("**", "").replace("##", "").replace("#", "")

    return prompt.strip()

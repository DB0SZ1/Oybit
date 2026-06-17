"""
Persona Prompt Builder — Agent A Module

Reads persona.md + simulation_log.md + topic brief + platform rules.
Returns structured system prompt + user prompt for OpenRouter generation call.
"""

import os
import re
from pathlib import Path

# The directory where all strategy markdowns are stored
STRATEGY_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "persona_data")


def _read_file_safe(path: str) -> str:
    """Read file content, return empty string if not found."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except (FileNotFoundError, IOError):
        return ""


def _get_last_n_sim_entries(sim_log_content: str, n: int = 10) -> str:
    """Extract the last N simulation log entries."""
    if not sim_log_content.strip():
        return "(No simulation log entries yet)"

    # Split by ### Sim markers
    entries = re.split(r'(?=### Sim\s)', sim_log_content)
    entries = [e.strip() for e in entries if e.strip() and e.strip().startswith("### Sim")]
    
    if not entries:
        return "(No simulation log entries yet)"

    last_n = entries[-n:]
    return "\n\n".join(last_n)


def _get_platform_tone(persona_content: str, platform: str) -> str:
    """Extract platform-specific tone modifier from persona.md."""
    tone_map = {
        "instagram_personal": "Personal Instagram",
        "instagram_brand": "Brand Instagram",
        "linkedin": "LinkedIn",
        "facebook": "Facebook",
    }

    label = tone_map.get(platform, platform)
    
    # Find the tone section for this platform
    pattern = rf'\*\*{re.escape(label)}.*?\*\*\s*\n(.*?)(?=\n\*\*|\n---|\n## |\Z)'
    match = re.search(pattern, persona_content, re.DOTALL)
    if match:
        return match.group(1).strip()
    return f"Standard tone for {platform}"


def _get_hard_stops(persona_content: str) -> str:
    """Extract hard stops list from persona.md."""
    match = re.search(
        r'Hard stops.*?never post about.*?\n((?:- .*\n?)+)',
        persona_content,
        re.IGNORECASE
    )
    if match:
        return match.group(1).strip()
    return "- No hard stops configured"


def _get_voice_section(persona_content: str) -> str:
    """Extract the Voice & Tone section from persona.md."""
    match = re.search(
        r'## 2\. Voice & Tone\s*\n(.*?)(?=\n## \d|\Z)',
        persona_content,
        re.DOTALL
    )
    if match:
        return match.group(1).strip()
    return "(Voice section not found in persona.md)"


def build_prompt(
    persona_path: str,
    simulation_log_path: str,
    topic_brief: str,
    platform: str,
    format_type: str = "text",
    account: str = None,
) -> dict:
    """
    Build structured system prompt + user prompt for content generation.

    Args:
        persona_path: absolute path to persona.md
        simulation_log_path: absolute path to simulation_log.md
        topic_brief: the topic brief text to generate content for
        platform: target platform (linkedin, instagram_personal, instagram_brand, facebook)
        format_type: content format (text, carousel, video, image)
        account: specific account name (defaults to platform)

    Returns:
        dict with keys: system_prompt, user_prompt
    """
    if account is None:
        account = platform

    # Read full persona.md every call
    persona_content = _read_file_safe(persona_path)
    if not persona_content:
        raise FileNotFoundError(f"CRITICAL: persona.md not found at {persona_path}. The engine cannot proceed without a persona.")

    # Read simulation_log.md and get last 10 entries
    sim_log_content = _read_file_safe(simulation_log_path)
    last_10_entries = _get_last_n_sim_entries(sim_log_content, n=10)

    # Extract key sections
    voice_section = _get_voice_section(persona_content)
    platform_tone = _get_platform_tone(persona_content, platform)
    hard_stops = _get_hard_stops(persona_content)

    # Platform-specific rules
    platform_rules = {
        "linkedin": "Maximum 1300 characters. No hashtag spam. Thought leadership register. Technical storytelling. No exclamation marks.",
        "instagram_personal": "Hook in first line — must grab attention in 1 sentence. Casual tone. Relatable. Trending audio awareness for Reels. Nigerian colloquialisms acceptable.",
        "instagram_brand": "Product-first. Aesthetic. Nyvora voice. Professional but not corporate. No personal anecdotes.",
        "facebook": "Longer form acceptable. Discussion-oriented. Community angle. End with a discussion question.",
    }
    
    format_rules = {
        "text": "Plain text post. No markdown formatting. No code blocks. Structure with line breaks.",
        "carousel": "Generate slide-by-slide content. Each slide: headline (max 8 words) + body (max 30 words). 5-10 slides. First slide is the hook. If a slide needs a 3D visual, include a marker `[LOTTIE: <noun>]` (e.g., `[LOTTIE: rocket]`, `[LOTTIE: chart]`).",
        "video": "Generate script with scene breakdown. Hook in first 3 seconds. Kinetic typography style. 30-60 second duration. If a scene needs a 3D visual, include a marker `[LOTTIE: <noun>]`.",
        "image": "Generate accompanying caption text. Hook-first.",
    }

    # Fetch dynamic strategy files - Read ALL .md files in the strategy directory
    strategy_blocks = ""
    strategy_files_found = 0
    
    if os.path.exists(STRATEGY_DIR):
        for filename in os.listdir(STRATEGY_DIR):
            if filename.endswith(".md"):
                file_path = os.path.join(STRATEGY_DIR, filename)
                content = _read_file_safe(file_path)
                if content:
                    strategy_files_found += 1
                    strategy_blocks += f"\n=== STRATEGY: {filename.upper()} ===\n{content.strip()}\n"
                    
    if strategy_files_found == 0:
        raise FileNotFoundError(f"CRITICAL: No strategy files found in {STRATEGY_DIR}. The engine requires at least one strategy file to proceed.")

    # Build system prompt
    system_prompt = f"""You are generating content for Ahmad's {platform} account.

=== PERSONA VOICE ===
{voice_section}
{strategy_blocks}
=== PLATFORM TONE MODIFIER ({platform.upper()}) ===
{platform_tone}

=== CONTENT DNA REQUIREMENT ===
Every post MUST contain at least ONE of these elements:
- System insight: reveals how something actually works
- Real consequence: something that happened or will happen
- Technical mechanism: the specific thing that caused it  
- Contradiction: something unexpected or counterintuitive
Posts without any DNA element will be REJECTED. No exceptions.

=== WINNING POST STRUCTURE ===
Follow this proven structure:
Real situation → system insight → constraint/lesson → relatable framing → minimal CTA

=== HARD STOPS (never include) ===
{hard_stops}

=== PLATFORM RULES ===
{platform_rules.get(platform, "Standard platform rules apply.")}

=== FORMAT RULES ===
{format_rules.get(format_type, "Standard text format.")}

=== RECENT BEHAVIORAL INSIGHTS (from simulation log) ===
{last_10_entries}

=== INSTRUCTIONS ===
Generate between 5 and 20 variants of this post. Each variant should:
1. Use a different hook style (question, statistic, personal incident, bold claim, story opener)
2. Maintain Ahmad's authentic voice throughout
3. Include at least one Content DNA element
4. Follow the winning post structure
5. Respect all hard stops

Return each variant separated by "---VARIANT---" markers.
Do NOT include variant numbers or labels — just the raw content."""

    # Build user prompt
    user_prompt = f"""Generate {format_type} content for {platform}.

Topic Brief:
{topic_brief}

Target Account: {account}
Format: {format_type}

Generate 5-20 variants with different hook styles and angles. Each variant must contain at least one Content DNA element (system insight, real consequence, technical mechanism, or contradiction)."""

    return {
        "system_prompt": system_prompt,
        "user_prompt": user_prompt,
    }


# Alias for the interface expected by generator.py
def assemble_generation_prompt(
    persona_path: str,
    simulation_log_path: str,
    topic_brief: str,
    platform: str,
    format_type: str = "text",
    account: str = None,
) -> dict:
    """Alias for build_prompt — matches the interface spec in AGENTS.md."""
    return build_prompt(
        persona_path=persona_path,
        simulation_log_path=simulation_log_path,
        topic_brief=topic_brief,
        platform=platform,
        format_type=format_type,
        account=account,
    )

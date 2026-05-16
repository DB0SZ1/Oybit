"""
Oybit — Waitlist & Onboarding (GAPS_FINAL GAPs 5.1–5.3)
Waitlist capture, persona template, onboarding simulation.
"""
import json
import logging
import os
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

# ── GAP 5.1: Waitlist Capture Mechanism ───────────────────────
WAITLIST_PATH = Path(os.getenv("WAITLIST_PATH", "/data/waitlist.jsonl"))

def add_to_waitlist(email: str, name: str = "", source: str = "website") -> dict:
    """Add a user to the Oybit waitlist."""
    WAITLIST_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    entry = {
        "email": email,
        "name": name,
        "source": source,
        "signed_up_at": datetime.utcnow().isoformat() + "Z",
        "status": "pending"
    }
    
    # Check for duplicates
    if WAITLIST_PATH.exists():
        for line in WAITLIST_PATH.read_text('utf-8').strip().split('\n'):
            if line and json.loads(line).get("email") == email:
                return {"success": False, "reason": "already_registered"}
    
    with open(WAITLIST_PATH, 'a', encoding='utf-8') as f:
        f.write(json.dumps(entry) + '\n')
    
    return {"success": True, "position": get_waitlist_count()}

def get_waitlist_count() -> int:
    if not WAITLIST_PATH.exists():
        return 0
    return sum(1 for line in WAITLIST_PATH.read_text('utf-8').strip().split('\n') if line)


# ── GAP 5.2: Persona Template ─────────────────────────────────
PERSONA_TEMPLATE = """# {name} — Persona Profile

## Identity
- **Full Name**: {name}
- **Role**: {role}
- **Company**: {company}
- **Location**: {location}

## Voice & Tone
- **Writing Style**: {writing_style}
- **Signature Phrases**: {signature_phrases}
- **Avoid**: {avoid_phrases}

## Content Pillars
{content_pillars}

## Platform-Specific Notes
### Instagram
- Visual-first, use carousel for educational content
- Reels for behind-the-scenes and quick tips

### LinkedIn
- Long-form, value-driven posts
- Never start first line with "I"
- Polls for engagement on strategy topics

### Facebook
- Group-focused distribution
- Reels for reach, text for engagement

## Audience
- **Primary**: {primary_audience}
- **Secondary**: {secondary_audience}

## Current Goals
{current_goals}

## Topics to Avoid
{topics_to_avoid}
"""

def generate_persona_file(config: dict) -> str:
    """Generate a persona.md file from a config dict."""
    pillars = "\n".join(f"- {p}" for p in config.get("content_pillars", []))
    goals = "\n".join(f"- {g}" for g in config.get("current_goals", []))
    avoid = "\n".join(f"- {a}" for a in config.get("topics_to_avoid", []))
    
    return PERSONA_TEMPLATE.format(
        name=config.get("name", ""),
        role=config.get("role", ""),
        company=config.get("company", ""),
        location=config.get("location", ""),
        writing_style=config.get("writing_style", ""),
        signature_phrases=", ".join(config.get("signature_phrases", [])),
        avoid_phrases=", ".join(config.get("avoid_phrases", [])),
        content_pillars=pillars,
        primary_audience=config.get("primary_audience", ""),
        secondary_audience=config.get("secondary_audience", ""),
        current_goals=goals,
        topics_to_avoid=avoid
    )


# ── GAP 5.3: Onboarding Simulation ───────────────────────────
def run_onboarding_simulation(persona_path: str, dry_run: bool = True) -> dict:
    """
    Run a public-content-mode simulation to validate persona before going live.
    Generates sample content without publishing.
    """
    from backend.content.generator import generate_content
    
    results = {"posts_generated": 0, "samples": [], "errors": []}
    
    platforms = ["instagram_personal", "linkedin", "facebook"]
    topics = ["Introduction post", "Industry insight", "Personal story"]
    
    for platform in platforms:
        for topic in topics:
            try:
                prompt_dict = {
                    "system_prompt": f"Generate a sample {platform} post about: {topic}",
                    "user_prompt": f"Write a {platform} post about {topic}. Keep it authentic."
                }
                variants = generate_content(prompt_dict, dry_run=True)
                results["posts_generated"] += 1
                results["samples"].append({
                    "platform": platform,
                    "topic": topic,
                    "content": variants.get(platform, list(variants.values())[0] if variants else "")[:200]
                })
            except Exception as e:
                results["errors"].append(f"{platform}/{topic}: {str(e)}")
    
    return results

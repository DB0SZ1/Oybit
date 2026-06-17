"""
Persona Builder — Agent A Module

Takes onboarding answers (dict of all stage responses).
Builds structured persona.md file using the template from persona_learning_and_trend_engine.md.
Writes to /data/personas/ahmad/persona.md
Creates empty simulation_log.md with header.
"""

import os
from datetime import datetime


PERSONA_TEMPLATE = """# Ahmad Idris Rabiu — Persona

_Version: 1 | Last updated: {timestamp} | Strategy: Initial baseline from onboarding_

---

## 1. Identity

**Full name:** {full_name}
**Brand name:** {brand_name}
**Mission:** {mission}
**Values:** {values}
**Origin:** {origin}
**We stand for:** {stand_for}
**We stand against:** {stand_against}

---

## 2. Voice & Tone

**Formality scale:** {formality_scale}
**Signature phrases:** {signature_phrases}
**Vocabulary always used:** {vocab_always}
**Vocabulary never used:** {vocab_never}
**Punctuation style:** {punctuation_style}
**Sentence length:** {sentence_length}
**Emoji use:** {emoji_use}
**Humour:** {humour}
**Swearing:** {swearing}
**Language:** {language}

---

## 3. Audience

**Primary:** {audience_primary}
**Secondary:** {audience_secondary}
**Tertiary:** {audience_tertiary}

**Pain points:**
{pain_points}

**Language they use:**
{audience_language}

**What they come to you for:**
{come_for}

**What they never want to see:**
{never_want}

---

## 4. Content Pillars

{content_pillars_table}

**Hard stops — never post about:**
{hard_stops}

---

## 5. Per-Account Tone Modifiers

**Personal Instagram:**
{tone_personal_ig}

**Brand Instagram (Nyvora):**
{tone_brand_ig}

**LinkedIn:**
{tone_linkedin}

**Facebook:**
{tone_facebook}

---

## 6. Engagement Style

**Reply tone:** {reply_tone}
**Praise:** {praise_style}
**Criticism:** {criticism_style}
**Debate:** {debate_style}
**Spam/negativity:** {spam_style}

**Per-account reply automation:**
- Personal IG: {reply_auto_personal_ig}
- Brand IG: {reply_auto_brand_ig}
- LinkedIn: {reply_auto_linkedin}
- Facebook: {reply_auto_facebook}

---

## 7. Performance Memory

_Updated automatically by learning engine_

**Top performing content types:**

| Account | Best format | Best pillar | Best hook type | Avg engagement score |
|---|---|---|---|---|
| Personal IG | — | — | — | — |
| Brand IG | — | — | — | — |
| LinkedIn | — | — | — | — |
| Facebook | — | — | — | — |

**Engagement benchmarks:**

| Account | Followers | Avg reach | Avg engagement score |
|---|---|---|---|
| Personal IG | 0 | 0 | 0 |
| Brand IG | 0 | 0 | 0 |
| LinkedIn | 0 | 0 | 0 |
| Facebook | 0 | 0 | 0 |

**Strategy history:**

| Version | Date | Trigger | Change |
|---|---|---|---|
| 1 | {date} | Initial | Baseline from onboarding |

**Current strategy focus:** Build audience through authentic technical storytelling
**Next rotation check:** {next_rotation}
"""

SIMULATION_LOG_HEADER = """# simulation_log.md — Ahmad
# APPEND-ONLY. Never modified. Only added to.
# Read by persona_engine/prompt_builder.py on every generation call.

---
"""

# Default values for Ahmad based on product.md
DEFAULT_ANSWERS = {
    "full_name": "Idris Rabiu Ahmad",
    "brand_name": "Ahmad (personal) / Nyvora (brand)",
    "mission": "Build real software products that solve real problems. Document the journey publicly. Prove it's possible from Abuja.",
    "values": "Execution over talk, systems over hustle, honesty over hype, African excellence, financial independence through product revenue",
    "origin": "18yo CS student at University of Abuja. Building Nyvora solo. Products shipped: ColdSift, Folio, Queryon, Niche, OutreachBot.",
    "stand_for": "Real work. Technical depth. African founders getting visibility. Automation that works unattended. Products that pay for themselves.",
    "stand_against": "Hype without proof. Vague announcements. Coming soon posts. Generic tips. Copying without attribution.",
    "formality_scale": "4/10 (personal IG) → 6/10 (LinkedIn) → 7/10 (brand IG)",
    "signature_phrases": "shipped, building from Abuja, real products",
    "vocab_always": "system, pipeline, shipped, automation, consequence, mechanism, Abuja, Nyvora, building, real",
    "vocab_never": "hustle, grind harder, mindset, level up, bro, crushing it, synergy, paradigm shift",
    "punctuation_style": "Short sentences. Periods after fragments. Dashes for emphasis — like this. Commas sparingly. Never exclamation marks on LinkedIn.",
    "sentence_length": "Short to medium. Fragments acceptable and frequent.",
    "emoji_use": "Rare on LinkedIn. Occasional on Instagram personal. Never on brand IG.",
    "humour": "Dry, understated. Never forced.",
    "swearing": "Never in posts. Fine in DMs.",
    "language": "English. Nigerian colloquialisms acceptable in personal IG.",
    "audience_primary": "Nigerian and African developers and founders (20–35)",
    "audience_secondary": "International indie hackers, build-in-public community",
    "audience_tertiary": "LinkedIn tech professionals (30–45)",
    "pain_points": "- Building real things but getting zero visibility\n- Payment friction as an African developer\n- Feeling isolated while building — no community, no validation\n- Imposter syndrome amplified by geography",
    "audience_language": '- "Building from Africa"\n- "solo founder"\n- "shipped it"\n- "side project"\n- "indie hacker"',
    "come_for": "- Proof that it's possible to build real products from Nigeria\n- Technical lessons they can actually apply\n- Honest takes — not polished success theatre",
    "never_want": '- Another vague "exciting things coming" post\n- Motivation content without substance\n- Engagement bait',
    "content_pillars_table": """| Pillar | Description | Personal IG | Brand IG | LinkedIn | Facebook |
|---|---|---|---|---|---|
| Technical systems | Security, pipelines, architecture, code stories | 20% | 10% | 25% | 15% |
| Building in public | Real product decisions, real outcomes, raw process | 25% | 25% | 20% | 20% |
| African founder perspective | Abuja, Nigeria, payment friction, African tech | 20% | 20% | 15% | 20% |
| Nyvora product updates | ColdSift, Oybit, Volari Finance milestones | 10% | 45% | 10% | 15% |
| Personal grind | 2AM moments, wins, honest failures | 10% | 0% | 10% | 10% |
| Opinions & Hot Takes | Strong industry takes, controversial thoughts, unfiltered opinions | 15% | 0% | 20% | 20% |""",
    "hard_stops": "- Specific relationship details\n- Financial figures (revenue, exact costs)\n- Political opinions\n- Religious content\n- Competitor criticism by name",
    "tone_personal_ig": 'Raw, casual, relatable. "This is my life building stuff." First person, present tense. Trending audio acknowledged. Abuja context welcome.',
    "tone_brand_ig": 'Polished, product-first, authoritative. "This is what Nyvora is building." Third-person brand references acceptable. No personal anecdotes.',
    "tone_linkedin": "Systems thinker, technical authority, honest founder. Lessons earned not borrowed. Data and specifics over generalities. Always a concrete mechanism or consequence.",
    "tone_facebook": "LinkedIn content adapted. Add discussion question at end. Slightly more accessible. Wider audience assumed.",
    "reply_tone": "Direct, uses personal proof, non-defensive",
    "praise_style": "Acknowledge briefly, don't dwell",
    "criticism_style": "Address the technical point, not the emotion",
    "debate_style": "Engage if there's a real technical disagreement. Disengage from bad faith.",
    "spam_style": "Ignore. Never feed.",
    "reply_auto_personal_ig": "AI drafts, Ahmad approves",
    "reply_auto_brand_ig": "AI drafts, Ahmad approves",
    "reply_auto_linkedin": "AI drafts, Ahmad approves",
    "reply_auto_facebook": "Full auto for positive comments, manual for complaints",
}


def build_persona(answers: dict, persona_dir: str = None) -> dict:
    """
    Build persona.md from onboarding answers.

    Args:
        answers: dict of onboarding answer values (keys match template placeholders)
        persona_dir: directory to write files to (defaults to PERSONA_DIR from config)

    Returns:
        dict with keys: persona_path, simulation_log_path, success, error

    Raises:
        FileExistsError if persona.md already exists (never overwrite)
    """
    if persona_dir is None:
        try:
            from config import PERSONA_DIR
            persona_dir = PERSONA_DIR
        except ImportError:
            persona_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "personas", "ahmad")

    os.makedirs(persona_dir, exist_ok=True)

    persona_path = os.path.join(persona_dir, "persona.md")
    sim_log_path = os.path.join(persona_dir, "simulation_log.md")

    # Check if persona.md already exists - never overwrite
    if os.path.exists(persona_path):
        return {
            "persona_path": persona_path,
            "simulation_log_path": sim_log_path,
            "success": False,
            "error": "persona.md already exists. Use updater.py to modify it.",
        }

    # Merge defaults with provided answers
    merged = {**DEFAULT_ANSWERS, **answers}
    now = datetime.utcnow()
    merged["timestamp"] = now.isoformat()
    merged["date"] = now.strftime("%Y-%m-%d")

    # Calculate next rotation check: 14 days from now
    from datetime import timedelta
    merged["next_rotation"] = (now + timedelta(days=14)).strftime("%Y-%m-%d")

    # Render persona.md
    persona_content = PERSONA_TEMPLATE.format(**merged)
    with open(persona_path, "w", encoding="utf-8") as f:
        f.write(persona_content)

    # Create empty simulation_log.md
    with open(sim_log_path, "w", encoding="utf-8") as f:
        f.write(SIMULATION_LOG_HEADER)

    return {
        "persona_path": persona_path,
        "simulation_log_path": sim_log_path,
        "success": True,
        "error": None,
    }

"""
Oybit — Template Selector
Routes each post to the best carousel template based on:
  - account type
  - hook type
  - topic pillar
  - content mood / energy

Supports 6 template designs:
  1. carousel_personal_ig.html  — Dark tech (IG personal default)
  2. carousel_glass.html        — Glassmorphism (high-engagement topics)
  3. carousel_brutalist.html    — Editorial brutalist (authority/contrarian)
  4. carousel_gradient.html     — Vivid gradient (storytelling/emotional)
  5. carousel_brand_ig.html     — Brand card layout (IG brand default)
  6. carousel_linkedin.html     — Clean professional (LinkedIn default)
"""
import random
import logging

logger = logging.getLogger(__name__)

# ── Template Catalog ──────────────────────────────────
TEMPLATES = {
    "personal_dark": {
        "file": "carousel_personal_ig.html",
        "mood": "technical, build-in-public, coding, startup",
        "energy": "focused",
    },
    "glass": {
        "file": "carousel_glass.html",
        "mood": "premium, insight, deep-dive, strategy",
        "energy": "elevated",
    },
    "brutalist": {
        "file": "carousel_brutalist.html",
        "mood": "contrarian, opinion, hot-take, truth-bomb",
        "energy": "bold",
    },
    "gradient": {
        "file": "carousel_gradient.html",
        "mood": "storytelling, journey, emotional, growth",
        "energy": "dynamic",
    },
    "brand_card": {
        "file": "carousel_brand_ig.html",
        "mood": "product, brand, business, professional",
        "energy": "polished",
    },
    "linkedin_clean": {
        "file": "carousel_linkedin.html",
        "mood": "thought-leadership, professional, B2B, career",
        "energy": "refined",
    },
    "trending_take": {
        "file": "trending_take.html",
        "mood": "trending, news, hot-take, external-source",
        "energy": "loud",
    },
}

# ── Account → Default Template Mapping ────────────────
ACCOUNT_DEFAULTS = {
    "instagram_personal": "personal_dark",
    "instagram_brand": "brand_card",
    "linkedin": "linkedin_clean",
    "facebook": "gradient",
}

# ── Hook Type → Template Preference ──────────────────
HOOK_PREFERENCES = {
    "contrarian": "brutalist",
    "question": "glass",
    "number_hook": "brand_card",
    "story_hook": "gradient",
    "this_or_that": "brutalist",
    "myth_buster": "brutalist",
    "data_drop": "linkedin_clean",
    "vulnerability": "gradient",
    "build_in_public": "personal_dark",
    "tutorial": "personal_dark",
    "industry_insight": "glass",
    "case_study": "brand_card",
}

# ── Topic Pillar → Template Preference ────────────────
PILLAR_PREFERENCES = {
    "ai_automation": "personal_dark",
    "saas_building": "personal_dark",
    "founder_journey": "gradient",
    "leadership": "linkedin_clean",
    "product_launch": "brand_card",
    "market_analysis": "glass",
    "culture_opinion": "brutalist",
    "growth_strategy": "glass",
}


def select_template(
    account: str,
    hook_type: str = None,
    topic_pillar: str = None,
    style_override: str = None,
    variety_mode: bool = True,
) -> dict:
    """
    Select the best carousel template for a post.
    
    Priority: style_override > hook_type > topic_pillar > account_default
    
    If variety_mode is True and we would pick the same template 3 times 
    in a row, we randomize from the 2 runner-ups.
    
    Returns:
        dict with 'template_file', 'template_key', 'reason'
    """
    # 1. Explicit override
    if style_override and style_override in TEMPLATES:
        return _result(style_override, "explicit override")
    
    # 2. Hook-type based
    if hook_type and hook_type.lower() in HOOK_PREFERENCES:
        key = HOOK_PREFERENCES[hook_type.lower()]
        return _result(key, f"hook_type: {hook_type}")
    
    # 3. Topic-pillar based
    if topic_pillar:
        pillar_key = topic_pillar.lower().replace(" ", "_").replace("-", "_")
        if pillar_key in PILLAR_PREFERENCES:
            key = PILLAR_PREFERENCES[pillar_key]
            return _result(key, f"topic_pillar: {topic_pillar}")
    
    # 4. Account default
    account_key = account.lower() if account else "instagram_personal"
    if account_key in ACCOUNT_DEFAULTS:
        key = ACCOUNT_DEFAULTS[account_key]
        
        # Variety mode: 20% chance to pick a different template
        # to keep the feed visually diverse
        if variety_mode and random.random() < 0.2:
            alternatives = _get_alternatives(key, account_key)
            if alternatives:
                alt_key = random.choice(alternatives)
                return _result(alt_key, f"variety_mode (default was {key})")
        
        return _result(key, f"account_default: {account_key}")
    
    # 5. Fallback
    return _result("personal_dark", "fallback")


def _get_alternatives(current_key: str, account: str) -> list:
    """Get alternative templates that still work for this account."""
    if account in ("instagram_personal", "instagram_brand"):
        # IG supports all templates
        return [k for k in TEMPLATES if k != current_key]
    elif account == "linkedin":
        # LinkedIn should stay clean
        return ["glass", "brand_card"]
    elif account == "facebook":
        return ["glass", "gradient", "personal_dark"]
    return []


def _result(key: str, reason: str) -> dict:
    template = TEMPLATES[key]
    logger.info(f"Template selected: {key} ({template['file']}) — {reason}")
    return {
        "template_file": template["file"],
        "template_key": key,
        "energy": template["energy"],
        "reason": reason,
    }


def get_template_context(
    post: dict,
    template_key: str = None,
) -> dict:
    import random
    account = post.get("account", "instagram_personal")
    
    # Randomize the highlight color
    highlights = ["#C15F3C", "#2cb651"]
    primary_color = random.choice(highlights)
    
    # Secondary color is a slightly darker/desaturated version for gradients
    secondary_color = "#9c4a2e" if primary_color == "#C15F3C" else "#228b3e"
    
    # Brand identity defaults per account
    brand_configs = {
        "instagram_personal": {
            "brand_color_primary": primary_color,
            "brand_color_secondary": secondary_color,
            "handle": "ahmad",
            "author_name": "Ahmad",
            "author_title": "Building in public",
        },
        "instagram_brand": {
            "brand_color_primary": primary_color,
            "brand_color_secondary": secondary_color,
            "brand_name": "NYVORA",
            "brand_url": "nyvora.com",
            "handle": "nyvora",
        },
        "linkedin": {
            "brand_color_primary": primary_color,
            "brand_color_secondary": secondary_color,
            "author_name": "Ahmad",
            "author_title": "Founder @ Nyvora",
            "handle": "ahmad",
        },
        "facebook": {
            "brand_color_primary": primary_color,
            "brand_color_secondary": secondary_color,
            "handle": "ahmad",
            "author_name": "Ahmad",
        },
    }
    
    config = brand_configs.get(account, brand_configs["instagram_personal"])
    
    # Gradient-specific colors
    if template_key == "gradient":
        config["gradient_from"] = config.get("brand_color_primary", "#667eea")
        config["gradient_via"] = "#764ba2"
        config["gradient_to"] = "#f093fb"
    
    context = {
        **config,
        "font_family": "'Inter', sans-serif",
        "topic_pillar": post.get("topic_pillar", ""),
        "cta_text": post.get("cta_text", "Follow for more →"),
        "logo_url": post.get("logo_url", ""),
    }
    
    return context


def parse_slides_from_content(content_text: str) -> list[dict]:
    """
    Parse a content text block into slide-sized chunks for carousel rendering.
    
    Splits on:
      1. Explicit slide markers: [SLIDE], ---
      2. Double newlines (paragraph breaks)
      3. Smart fallback: sentences
    
    Returns list of {"headline": str, "body": str, "lottie_url": str}
    """
    if not content_text:
        return [{"headline": "Coming soon", "body": "", "lottie_url": ""}]
        
    import re
    from backend.render_engine.asset_manager import resolve_lottie_keyword
    
    text = content_text.strip()
    
    # Strategy 1: Explicit slide markers
    if "[SLIDE]" in text or "\n---\n" in text:
        parts = text.replace("[SLIDE]", "---").split("---")
        slides = []
        for part in parts:
            part = part.strip()
            if not part:
                continue
            lines = part.split("\n", 1)
            headline = lines[0].strip().lstrip("#").strip()
            body = lines[1].strip() if len(lines) > 1 else ""
            slides.append({"headline": headline, "body": body})
        parsed_slides = slides if slides else [{"headline": text[:100], "body": ""}]
    
    # Strategy 2: Paragraph-based splitting
    elif len([p.strip() for p in text.split("\n\n") if p.strip()]) >= 3:
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        slides = []
        for p in paragraphs:
            lines = p.split("\n", 1)
            # First sentence as headline (up to ~80 chars)
            first_line = lines[0].strip()
            if len(first_line) > 100:
                # Split at first period or comma
                for sep in [". ", ", ", " — ", " – "]:
                    if sep in first_line[:80]:
                        idx = first_line.index(sep, 0, 80)
                        headline = first_line[:idx + 1].strip()
                        body = first_line[idx + len(sep):].strip()
                        if len(lines) > 1:
                            body += "\n" + lines[1].strip()
                        slides.append({"headline": headline, "body": body})
                        break
                else:
                    slides.append({"headline": first_line[:80] + "...", "body": first_line[80:]})
            else:
                body = lines[1].strip() if len(lines) > 1 else ""
                slides.append({"headline": first_line, "body": body})
        
        parsed_slides = slides[:10]  # Max 10 slides
    
    # Strategy 3: Sentence-based for short content
    else:
        sentences = re.split(r'(?<=[.!?])\s+', text)
        if len(sentences) >= 2:
            slides = []
            for s in sentences:
                s = s.strip()
                if len(s) > 15:  # Skip fragments
                    slides.append({"headline": s, "body": ""})
            parsed_slides = slides[:8] if slides else [{"headline": text[:100], "body": ""}]
        else:
            parsed_slides = [{"headline": text[:100], "body": text[100:] if len(text) > 100 else ""}]

    # Final Pass: Extract [LOTTIE: keyword] tags from all parsed slides
    lottie_pattern = re.compile(r'\[LOTTIE:\s*([^\]]+)\]', re.IGNORECASE)
    
    for slide in parsed_slides:
        slide["lottie_url"] = ""
        
        # Check headline
        match_hl = lottie_pattern.search(slide["headline"])
        if match_hl:
            slide["lottie_url"] = resolve_lottie_keyword(match_hl.group(1))
            slide["headline"] = lottie_pattern.sub("", slide["headline"]).strip()
            
        # Check body
        match_bd = lottie_pattern.search(slide["body"])
        if match_bd:
            if not slide["lottie_url"]:  # Only grab the first one we find per slide
                slide["lottie_url"] = resolve_lottie_keyword(match_bd.group(1))
            slide["body"] = lottie_pattern.sub("", slide["body"]).strip()

    return parsed_slides

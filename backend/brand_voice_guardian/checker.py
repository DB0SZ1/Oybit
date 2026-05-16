"""
Brand Voice Guardian — Agent A Module

Runs on every candidate before rendering.
Returns CheckResult(passed, near_pass, rejected, edit_suggestion, rejection_reason).

Checks run IN ORDER (fail fast):
1. Content DNA check
2. Hard stops check
3. Tone similarity check (semantic similarity to persona voice)
4. Platform appropriateness (length, format, tone)
5. Brand safety check
"""

import os
import re
from dataclasses import dataclass
from backend.intelligence.content_dna_checker import check_content_dna
from backend.content.platform_rules import check_linkedin_specific_rules, validate_reel_caption_hook


@dataclass
class CheckResult:
    passed: bool
    near_pass: bool
    rejected: bool
    edit_suggestion: str
    rejection_reason: str


# Default hard stops
DEFAULT_HARD_STOPS = [
    "specific relationship details",
    "financial figures", "revenue", "exact costs",
    "political opinions", "politics",
    "religious content", "religion",
    "competitor criticism by name",
]

# Platform limits
PLATFORM_LIMITS = {
    "linkedin": {"max_chars": 1300, "name": "LinkedIn"},
    "instagram_personal": {"max_chars": 2200, "name": "Instagram Personal"},
    "instagram_brand": {"max_chars": 2200, "name": "Instagram Brand"},
    "facebook": {"max_chars": 63206, "name": "Facebook"},
}


# Ahmad's voice keywords for basic tone similarity
VOICE_KEYWORDS = [
    "system", "pipeline", "shipped", "automation", "consequence",
    "mechanism", "abuja", "nyvora", "building", "real",
    "built", "product", "deploy", "code", "api", "architecture",
    "learned", "discovered", "found", "realized",
    "security", "technical", "actually", "specific",
]

# Anti-patterns: words Ahmad would never use
ANTI_VOICE = [
    "hustle", "grind harder", "mindset", "level up", "bro",
    "crushing it", "synergy", "paradigm shift", "game changer",
    "circle back", "touch base", "thought leader", "guru",
    "hack your life", "boss babe", "rise and grind",
    "leverage", "disrupt", "pivot", "ideate",
]

# Brand safety red flags
BRAND_SAFETY_FLAGS = [
    "embarrass", "racist", "sexist", "hate", "scandal",
    "assault", "violence", "defam", "libel", "slander",
    "illegal", "fraud", "scam",
]


def _load_persona_data(persona_path: str = None) -> dict:
    """Load persona data for voice matching."""
    data = {
        "hard_stops": DEFAULT_HARD_STOPS,
        "voice_keywords": VOICE_KEYWORDS,
        "anti_voice": ANTI_VOICE,
    }
    
    if not persona_path or not os.path.exists(persona_path):
        return data
    
    try:
        with open(persona_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Extract hard stops
        match = re.search(
            r'Hard stops.*?never post about.*?\n((?:- .*\n?)+)',
            content, re.IGNORECASE
        )
        if match:
            stops = [line.strip().lstrip("- ").strip().lower() 
                     for line in match.group(1).strip().split("\n") if line.strip()]
            data["hard_stops"] = stops
        
        # Extract vocab always used
        match = re.search(r'Vocabulary always used:\*\*\s*(.*?)$', content, re.MULTILINE)
        if match:
            words = [w.strip().lower() for w in match.group(1).split(",")]
            data["voice_keywords"] = words
        
        # Extract vocab never used
        match = re.search(r'Vocabulary never used:\*\*\s*(.*?)$', content, re.MULTILINE)
        if match:
            words = [w.strip().lower() for w in match.group(1).split(",")]
            data["anti_voice"] = words
            
    except Exception:
        pass
    
    return data


def _compute_tone_similarity(text: str, voice_keywords: list, anti_voice: list) -> float:
    """
    Compute a basic tone similarity score (0-1).
    
    Uses keyword matching as a proxy for semantic similarity.
    Higher score = more aligned with Ahmad's voice.
    """
    if not text.strip():
        return 0.0
    
    text_lower = text.lower()
    words = set(re.findall(r'\b\w+\b', text_lower))
    
    # Positive: Ahmad's vocabulary present
    positive_hits = sum(1 for kw in voice_keywords if kw.lower() in text_lower)
    
    # Negative: anti-voice words present
    negative_hits = sum(1 for av in anti_voice if av.lower() in text_lower)
    
    # Calculate score
    total_words = max(len(words), 1)
    positive_ratio = min(positive_hits / max(len(voice_keywords), 1), 1.0)
    negative_penalty = min(negative_hits * 0.15, 0.6)
    
    # Base score from text characteristics (short sentences, fragments, etc.)
    sentences = re.split(r'[.!?]+', text)
    avg_sentence_len = sum(len(s.split()) for s in sentences if s.strip()) / max(len([s for s in sentences if s.strip()]), 1)
    
    # Ahmad uses short sentences (avg 8-15 words)
    sentence_bonus = 0.2 if 5 <= avg_sentence_len <= 18 else 0.0
    
    # Uses dashes for emphasis
    dash_bonus = 0.05 if "—" in text or " - " in text else 0.0
    
    score = 0.3 + positive_ratio * 0.4 + sentence_bonus + dash_bonus - negative_penalty
    return max(0.0, min(1.0, score))


def check_brand_voice(
    text: str,
    platform: str = "linkedin",
    persona_path: str = None,
    format_type: str = "text",
) -> CheckResult:
    """
    Run Brand Voice Guardian checks on a candidate post.
    
    Checks run IN ORDER (fail fast):
    1. Content DNA check
    2. Hard stops check
    3. Tone similarity check
    4. Platform appropriateness
    5. Brand safety
    
    Args:
        text: the candidate post text
        platform: target platform
        persona_path: path to persona.md
        format_type: content format (text, carousel, video, image)
        
    Returns:
        CheckResult with pass/near_pass/reject status
    """
    # Handle empty input
    if not text or not text.strip():
        return CheckResult(
            passed=False,
            near_pass=False,
            rejected=True,
            edit_suggestion="",
            rejection_reason="Empty content — nothing to check",
        )
    
    persona_data = _load_persona_data(persona_path)
    
    # CHECK 1: Content DNA (fail fast)
    dna_result = check_content_dna(text, use_ai=False)
    if not dna_result.passes:
        return CheckResult(
            passed=False,
            near_pass=False,
            rejected=True,
            edit_suggestion="",
            rejection_reason="Content DNA check failed — post contains no system insight, real consequence, technical mechanism, or contradiction. Every post must contain at least one DNA element.",
        )
    
    # CHECK 2: Hard stops (fail fast)
    text_lower = text.lower()
    for stop in persona_data["hard_stops"]:
        if stop.lower() in text_lower:
            return CheckResult(
                passed=False,
                near_pass=False,
                rejected=True,
                edit_suggestion="",
                rejection_reason=f"Hard stop violated — post contains topic '{stop}' which is on the never-post list.",
            )
    
    # CHECK 3: Tone similarity
    tone_score = _compute_tone_similarity(text, persona_data["voice_keywords"], persona_data["anti_voice"])
    if tone_score < 0.55:
        return CheckResult(
            passed=False,
            near_pass=False,
            rejected=True,
            edit_suggestion="",
            rejection_reason=f"Tone similarity too low ({tone_score:.2f} < 0.55) — this doesn't sound like Ahmad. Use shorter sentences, technical specifics, personal proof, and Ahmad's vocabulary.",
        )
    
    # CHECK 4: Platform appropriateness
    limits = PLATFORM_LIMITS.get(platform, {"max_chars": 5000, "name": platform})
    if len(text) > limits["max_chars"]:
        return CheckResult(
            passed=False,
            near_pass=True,
            rejected=False,
            edit_suggestion=f"Post is {len(text)} chars — {limits['name']} limit is {limits['max_chars']}. Trim by {len(text) - limits['max_chars']} characters. Focus on tightening the middle section.",
            rejection_reason="",
        )
        
    if platform == "linkedin":
        # GAP 11.2 - LinkedIn Algorithm Reality
        # LinkedIn algorithm penalizes external links in the body and generic formatting.
        if "http://" in text or "https://" in text:
            return CheckResult(passed=False, near_pass=True, rejected=False, edit_suggestion="Remove external links from the main body (LinkedIn penalty). Put the link in the comments.", rejection_reason="")
        li_issues = check_linkedin_specific_rules(text)
        if li_issues:
            return CheckResult(passed=False, near_pass=True, rejected=False, edit_suggestion=" ".join(li_issues), rejection_reason="")
            
    if platform == "facebook":
        # GAP 11.3 - Facebook Reality
        # Facebook algorithm heavily penalizes explicit engagement bait and prefers highly conversational tone.
        if re.search(r'\b(comment below|share this|tag a friend|like if you agree)\b', text_lower):
            return CheckResult(passed=False, near_pass=True, rejected=False, edit_suggestion="Remove explicit engagement bait (e.g., 'comment below', 'tag a friend'). Facebook penalizes this.", rejection_reason="")
    if format_type in ["reel", "video"] and platform in ["instagram_personal", "instagram_brand"]:
        reel_result = validate_reel_caption_hook(text)
        if not reel_result["passed"]:
            return CheckResult(passed=False, near_pass=True, rejected=False, edit_suggestion=reel_result["suggestion"], rejection_reason="")
    
    # CHECK 5: Brand safety
    for flag in BRAND_SAFETY_FLAGS:
        if flag.lower() in text_lower:
            return CheckResult(
                passed=False,
                near_pass=True,
                rejected=False,
                edit_suggestion=f"Brand safety flag: content may contain sensitive term '{flag}'. Review for potential misreading. Consider rephrasing to avoid controversy exposure.",
                rejection_reason="",
            )
    
    # All checks passed
    return CheckResult(
        passed=True,
        near_pass=False,
        rejected=False,
        edit_suggestion="",
        rejection_reason="",
    )

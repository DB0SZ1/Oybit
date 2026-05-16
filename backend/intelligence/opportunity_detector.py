"""
Opportunity Detector — Agent A Module

Takes MiroFish narrative forecast output.
Filters each narrative through persona.md lens:
  - relevance_to_persona > 0.6
  - Content DNA Rule passes
  - No hard stop topics
Output: list of ApprovedTopicBrief
"""

import os
import re
from dataclasses import dataclass, field
from backend.intelligence.content_dna_checker import check_content_dna


@dataclass
class ApprovedTopicBrief:
    topic: str
    angle: str
    dna_element: str
    target_accounts: list
    timing: str
    platform_notes: str


# Default hard stops from persona.md
DEFAULT_HARD_STOPS = [
    "relationship", "relationships", "dating",
    "revenue", "salary", "exact costs", "financial figures",
    "politics", "political",
    "religion", "religious",
    "competitor criticism",
]


def _load_hard_stops(persona_path: str = None) -> list:
    """Load hard stops from persona.md."""
    if not persona_path or not os.path.exists(persona_path):
        return DEFAULT_HARD_STOPS

    try:
        with open(persona_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        match = re.search(
            r'Hard stops.*?never post about.*?\n((?:- .*\n?)+)',
            content,
            re.IGNORECASE,
        )
        if match:
            stops = []
            for line in match.group(1).strip().split("\n"):
                line = line.strip().lstrip("- ").strip().lower()
                if line:
                    # Extract individual stop words/phrases
                    stops.extend([w.strip() for w in line.split(",")])
                    stops.append(line)
            return stops
        return DEFAULT_HARD_STOPS
    except Exception:
        return DEFAULT_HARD_STOPS


def _check_hard_stops(text: str, hard_stops: list) -> bool:
    """Returns True if a hard stop topic is found in the text."""
    text_lower = text.lower()
    for stop in hard_stops:
        if stop.lower() in text_lower:
            return True
    return False


def _determine_target_accounts(narrative: dict) -> list:
    """Determine which accounts this narrative should target."""
    accounts = []
    topic = narrative.get("topic", "").lower()
    relevance = narrative.get("relevance_to_persona", 0.0)
    
    # LinkedIn: technical systems, lessons, authority
    if any(kw in topic for kw in ["security", "api", "pipeline", "architecture", "code", "system", "tool", "ai"]):
        accounts.append("linkedin")
    
    # Personal IG: building in public, personal stories, relatable
    if any(kw in topic for kw in ["build", "ship", "launch", "founder", "personal", "africa", "abuja", "nigeria"]):
        accounts.append("instagram_personal")
    
    # Brand IG: product updates, Nyvora, milestones
    if any(kw in topic for kw in ["product", "nyvora", "milestone", "launch", "release"]):
        accounts.append("instagram_brand")
    
    # Facebook: discussion-worthy, community
    if any(kw in topic for kw in ["discuss", "community", "trend", "opinion", "debate"]):
        accounts.append("facebook")
    
    # Default: at least LinkedIn if nothing matched
    if not accounts:
        if relevance > 0.8:
            accounts = ["linkedin", "instagram_personal"]
        else:
            accounts = ["linkedin"]
    
    return accounts


def _extract_dna_element(dna_result) -> str:
    """Extract the primary DNA element name from a DNAResult."""
    elements = []
    if dna_result.has_system_insight:
        elements.append("system_insight")
    if dna_result.has_real_consequence:
        elements.append("real_consequence")
    if dna_result.has_technical_mechanism:
        elements.append("technical_mechanism")
    if dna_result.has_contradiction:
        elements.append("contradiction")
    return ", ".join(elements) if elements else "none"


def detect_opportunities(
    narratives: list,
    persona_path: str = None,
    relevance_threshold: float = 0.6,
) -> list:
    """
    Filter MiroFish narrative forecast through persona lens + Content DNA Rule.

    Args:
        narratives: list of dicts with keys: topic, relevance_to_persona, framing_suggestion,
                    resonant_angles, avoid_angles, confidence, predicted_peak
        persona_path: path to persona.md for hard stops loading
        relevance_threshold: minimum relevance score (default 0.6)

    Returns:
        list of ApprovedTopicBrief for narratives that pass all filters
    """
    if not narratives:
        return []

    hard_stops = _load_hard_stops(persona_path)
    approved = []

    for narrative in narratives:
        topic = narrative.get("topic", "")
        relevance = narrative.get("relevance_to_persona", 0.0)
        framing = narrative.get("framing_suggestion", "")
        angles = narrative.get("resonant_angles", [])
        timing = narrative.get("predicted_peak", "")

        # Filter 1: relevance threshold
        if relevance < relevance_threshold:
            continue

        # Filter 2: hard stops
        if _check_hard_stops(topic, hard_stops):
            continue
        if _check_hard_stops(framing, hard_stops):
            continue

        # Filter 3: Content DNA Rule
        check_text = f"{topic}. {framing}. {' '.join(angles) if angles else ''}"
        dna_result = check_content_dna(check_text, use_ai=False)
        if not dna_result.passes:
            continue

        # Passed all filters — create approved brief
        target_accounts = _determine_target_accounts(narrative)
        dna_element = _extract_dna_element(dna_result)

        # Build platform notes
        platform_notes_parts = []
        if narrative.get("avoid_angles"):
            platform_notes_parts.append(f"Avoid: {', '.join(narrative['avoid_angles'])}")
        if narrative.get("confidence", 0) > 0:
            platform_notes_parts.append(f"Confidence: {narrative['confidence']:.0%}")
        platform_notes = "; ".join(platform_notes_parts) if platform_notes_parts else ""

        approved.append(ApprovedTopicBrief(
            topic=topic,
            angle=framing,
            dna_element=dna_element,
            target_accounts=target_accounts,
            timing=timing,
            platform_notes=platform_notes,
        ))

    return approved

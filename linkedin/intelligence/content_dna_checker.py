"""
Content DNA Checker — Agent A Module

Standalone function called by both opportunity_detector and brand_voice_guardian.
Takes any text → classifies which DNA elements are present.

Content DNA Rule: Every post must contain at least one of:
  - system_insight: reveals how something actually works
  - real_consequence: something that happened or will happen
  - technical_mechanism: the specific thing that caused it
  - contradiction: something unexpected or counterintuitive
"""

from dataclasses import dataclass
import os
import json
import re

# Try to import httpx for OpenRouter calls, fallback to keyword-based
try:
    import httpx
    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False


@dataclass
class DNAResult:
    has_system_insight: bool
    has_real_consequence: bool
    has_technical_mechanism: bool
    has_contradiction: bool
    passes: bool


# Keyword patterns for local fallback when OpenRouter is unavailable
SYSTEM_INSIGHT_PATTERNS = [
    r'\b(how|why)\s+(it|this|that|the\s+\w+)\s+(actually\s+)?(works|functions|operates)',
    r'\b(reveals?|exposes?|shows?|uncovers?)\s+(how|what|why)',
    r'\b(behind\s+the\s+scenes?|under\s+the\s+hood)',
    r'\b(system|mechanism|architecture|pipeline|infrastructure)\s+(insight|design|works)',
    r'\b(the\s+real\s+reason|what\s+most\s+people\s+don.t\s+(know|realize|understand))',
    r'\b(turns?\s+out|discovered?|found\s+that|learned?\s+that)',
    r'\b(internally|behind)\b.*\b(process|work|function)',
]

REAL_CONSEQUENCE_PATTERNS = [
    r'\b(result(ed)?|caused|led\s+to|meant\s+that|consequence)',
    r'\b(blocked|banned|leaked|lost|cost\s+\$|broke|crashed|failed)',
    r'\b(happened|occurred|incident|outage)',
    r'\b(as\s+a\s+result|because\s+of\s+this|which\s+meant)',
    r'\b(got\s+(fired|blocked|banned|suspended|locked|hacked))',
    r'\b(data\s+(breach|leak|loss)|credentials?\s+leak)',
    r'\b(real\s+impact|actual\s+damage|tangible\s+effect)',
]

TECHNICAL_MECHANISM_PATTERNS = [
    r'\b(API|endpoint|function|method|algorithm|protocol|query|pipeline)',
    r'\b(the\s+specific\s+(thing|code|bug|issue|line|function))',
    r'\b(because\s+(the|a)\s+\w+\s+(was|were|is|are|sent|returned|called))',
    r'\b(root\s+cause|stack\s+trace|error\s+message|response\s+code)',
    r'\b(buffer|overflow|injection|race\s+condition|deadlock|memory\s+leak)',
    r'\b(implementation|codebase|repository|commit|deploy)',
    r'\b(built|shipped|wrote|coded|implemented|debugged)\s+(a|the|my|our)',
]

CONTRADICTION_PATTERNS = [
    r'\b(but\s+(actually|really|in\s+fact|turns\s+out))',
    r'\b(counterintuitive|unexpected|surprising|ironic|paradox)',
    r'\b(opposite|contrary|despite|even\s+though|although)',
    r'\b(thought\s+(it|this|that|we)\s+(was|would|could|should))',
    r'\b(everyone\s+(thinks?|assumes?|believes?|says?))\s+.{1,50}\s+(but|however|yet)',
    r'\b(myth|misconception|wrong|incorrect|false)\b',
    r'\b(not\s+what\s+(you|we|they|i)\s+(think|expect|assumed))',
]


def _check_patterns(text: str, patterns: list[str]) -> bool:
    """Check if any regex pattern matches in the text."""
    text_lower = text.lower()
    for pattern in patterns:
        if re.search(pattern, text_lower):
            return True
    return False


def _check_dna_with_openrouter(text: str) -> DNAResult:
    """Use OpenRouter API for AI-powered DNA classification."""
    api_key = os.getenv("OPENROUTER_API_KEY", "")
    if not api_key or not HAS_HTTPX:
        return _check_dna_local(text)

    prompt = f"""Analyze this text and determine which Content DNA elements are present.

Content DNA elements:
1. system_insight — reveals how something actually works (behind the scenes, internal mechanics)
2. real_consequence — something that happened or will happen as a real result
3. technical_mechanism — the specific technical thing that caused something
4. contradiction — something unexpected, counterintuitive, or that subverts assumptions

Text to analyze:
\"\"\"{text}\"\"\"

Respond with ONLY a JSON object (no markdown, no explanation):
{{"has_system_insight": true/false, "has_real_consequence": true/false, "has_technical_mechanism": true/false, "has_contradiction": true/false}}"""

    try:
        model = os.getenv("OPENROUTER_DEFAULT_MODEL", "meta-llama/llama-4-scout:free")
        from llm.generator import call_openrouter_raw
        content = call_openrouter_raw(
            system_prompt="You are a content analysis expert. Respond only with valid JSON.",
            prompt=prompt,
            model=model,
            temperature=0.1,
            max_tokens=200
        )
        # Clean markdown fences if present
        content = re.sub(r'^```(?:json)?\s*', '', content)
        content = re.sub(r'\s*```$', '', content)
        data = json.loads(content)

        has_si = bool(data.get("has_system_insight", False))
        has_rc = bool(data.get("has_real_consequence", False))
        has_tm = bool(data.get("has_technical_mechanism", False))
        has_ct = bool(data.get("has_contradiction", False))

        return DNAResult(
            has_system_insight=has_si,
            has_real_consequence=has_rc,
            has_technical_mechanism=has_tm,
            has_contradiction=has_ct,
            passes=any([has_si, has_rc, has_tm, has_ct]),
        )
    except Exception:
        # Fallback to local pattern matching
        return _check_dna_local(text)


def _check_dna_local(text: str) -> DNAResult:
    """Local keyword/regex-based DNA classification fallback."""
    if not text or not text.strip():
        return DNAResult(
            has_system_insight=False,
            has_real_consequence=False,
            has_technical_mechanism=False,
            has_contradiction=False,
            passes=False,
        )

    has_si = _check_patterns(text, SYSTEM_INSIGHT_PATTERNS)
    has_rc = _check_patterns(text, REAL_CONSEQUENCE_PATTERNS)
    has_tm = _check_patterns(text, TECHNICAL_MECHANISM_PATTERNS)
    has_ct = _check_patterns(text, CONTRADICTION_PATTERNS)

    return DNAResult(
        has_system_insight=has_si,
        has_real_consequence=has_rc,
        has_technical_mechanism=has_tm,
        has_contradiction=has_ct,
        passes=any([has_si, has_rc, has_tm, has_ct]),
    )


def check_content_dna(text: str, use_ai: bool = True) -> DNAResult:
    """
    Main entry point. Takes any text → classifies which DNA elements are present.

    Args:
        text: The content to analyze
        use_ai: If True, try OpenRouter first (falls back to local). If False, use local only.

    Returns:
        DNAResult with boolean flags for each DNA element and overall pass status.
    """
    if not text or not text.strip():
        return DNAResult(
            has_system_insight=False,
            has_real_consequence=False,
            has_technical_mechanism=False,
            has_contradiction=False,
            passes=False,
        )

    if use_ai:
        return _check_dna_with_openrouter(text)
    return _check_dna_local(text)

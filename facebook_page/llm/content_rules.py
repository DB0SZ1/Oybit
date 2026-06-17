"""
Oybit — Content Rules Engine (GAPS_FINAL GAPs 6.1–6.3)
Cross-platform variation enforcement, LinkedIn first-line rule, Instagram reel caption hook rule.
"""
import re
import logging
import hashlib

logger = logging.getLogger(__name__)

# ── GAP 6.1: Cross-Platform Content Variation Enforcement ─────
def enforce_variation(variants: dict[str, str], min_difference_pct: float = 30.0) -> dict:
    """
    Ensure content across platforms is sufficiently different.
    Returns warnings if variants are too similar.
    """
    warnings = []
    accounts = list(variants.keys())
    
    for i in range(len(accounts)):
        for j in range(i + 1, len(accounts)):
            a, b = accounts[i], accounts[j]
            similarity = _text_similarity(variants[a], variants[b])
            if similarity > (100 - min_difference_pct):
                warnings.append(
                    f"Content for {a} and {b} is {similarity:.0f}% similar "
                    f"(needs >{min_difference_pct:.0f}% difference)"
                )
    
    return {"valid": len(warnings) == 0, "warnings": warnings}

def _text_similarity(text_a: str, text_b: str) -> float:
    """Calculate simple word-overlap similarity percentage."""
    words_a = set(text_a.lower().split())
    words_b = set(text_b.lower().split())
    
    if not words_a or not words_b:
        return 0.0
    
    overlap = len(words_a & words_b)
    total = len(words_a | words_b)
    return (overlap / total) * 100 if total > 0 else 0.0


# ── GAP 6.2: LinkedIn First Line Never Starts With "I" ───────
def fix_linkedin_first_line(text: str) -> str:
    """Rewrite LinkedIn post if the first line starts with 'I'."""
    lines = text.split('\n')
    if not lines:
        return text
    
    first_line = lines[0].strip()
    
    # Check if starts with "I " or "I'" (not just any word starting with I)
    if re.match(r"^I[\s']", first_line):
        # Common rewrites
        rewrites = {
            r"^I think ": "Here's a thought: ",
            r"^I believe ": "One truth about ",
            r"^I've been ": "Something I noticed after ",
            r"^I just ": "Just ",
            r"^I learned ": "A lesson that changed everything: ",
            r"^I was ": "Picture this: ",
            r"^I recently ": "Recently, ",
            r"^I'm ": "",  # Just remove "I'm" and capitalize next word
        }
        
        for pattern, replacement in rewrites.items():
            if re.match(pattern, first_line, re.IGNORECASE):
                new_first = re.sub(pattern, replacement, first_line, count=1, flags=re.IGNORECASE)
                if not new_first:  # "I'm" case
                    remaining = re.sub(r"^I'm\s+", "", first_line)
                    new_first = remaining[0].upper() + remaining[1:] if remaining else first_line
                lines[0] = new_first
                logger.info({"event": "linkedin_first_line_rewritten", "before": first_line[:50], "after": new_first[:50]})
                return '\n'.join(lines)
        
        # Generic fallback: move "I" clause to second sentence
        lines[0] = f"Here's what matters: {first_line[2:]}" if len(first_line) > 2 else first_line
        return '\n'.join(lines)
    
    return text


# ── GAP 6.3: Instagram Reel Caption 125-Char Hook Rule ───────
def enforce_reel_hook(caption: str, max_hook_chars: int = 125) -> dict:
    """
    Validate and fix Instagram Reel caption hook.
    The first line (before the "more" fold) must be ≤125 characters.
    """
    lines = caption.split('\n')
    first_line = lines[0] if lines else ""
    
    if len(first_line) <= max_hook_chars:
        return {"valid": True, "caption": caption, "hook_length": len(first_line)}
    
    # Try to find a natural break point
    truncated = first_line[:max_hook_chars]
    
    # Break at last sentence end
    for sep in ['. ', '! ', '? ', '— ', ' - ']:
        last_sep = truncated.rfind(sep)
        if last_sep > max_hook_chars * 0.5:
            truncated = truncated[:last_sep + 1].strip()
            break
    else:
        # Break at last word boundary
        truncated = truncated.rsplit(' ', 1)[0] + "..."
    
    # Rebuild caption with truncated hook + rest
    remaining = first_line[len(truncated):].strip()
    if remaining:
        lines[0] = truncated
        lines.insert(1, remaining)
    else:
        lines[0] = truncated
    
    new_caption = '\n'.join(lines)
    
    return {
        "valid": False,
        "original_hook_length": len(first_line),
        "fixed_hook_length": len(truncated),
        "caption": new_caption,
        "warning": f"Hook truncated from {len(first_line)} to {len(truncated)} chars"
    }

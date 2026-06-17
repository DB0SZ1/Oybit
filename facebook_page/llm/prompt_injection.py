"""
Oybit — Prompt Injection Sanitizer
Prevents manipulated seed content (e.g. from Reddit or RSS) from hijacking the agent prompt.
(GAPS_AND_FIXES 6.8 / OYBIT_GAP_SOLUTIONS 8.1)
"""
import re

INJECTION_PATTERNS = [
    r"(?i)ignore (all )?previous instructions",
    r"(?i)system prompt",
    r"(?i)you are now",
    r"(?i)forget (all )?previous",
    r"(?i)instead (you should|print|say|output)",
    r"(?i)new rule:",
    r"(?i)override instructions",
    r"(?i)disregard (the )?above"
]

def sanitize_for_prompt(text: str) -> str:
    """
    Cleanses input text of common prompt injection vectors before passing to OpenRouter.
    Replaces injected commands with [removed].
    """
    if not text:
        return ""
        
    sanitized = text
    for pattern in INJECTION_PATTERNS:
        sanitized = re.sub(pattern, "[removed]", sanitized)
        
    return sanitized

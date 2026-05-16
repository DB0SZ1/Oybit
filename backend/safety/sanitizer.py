"""
Oybit — Prompt Injection Sanitizer (GAP 6.8)
Prevents malicious inputs from overriding system instructions.
"""

import re
import logging

logger = logging.getLogger(__name__)

# Patterns that indicate potential prompt injection
INJECTION_PATTERNS = [
    r"(?i)ignore previous instructions",
    r"(?i)ignore all previous instructions",
    r"(?i)disregard previous",
    r"(?i)you are now",
    r"(?i)new rule:",
    r"(?i)system prompt:",
    r"(?i)forget everything",
    r"(?i)override system",
    r"(?i)bypass restrictions",
    r"(?i)switch to mode",
]

def sanitize_input(text: str) -> str:
    """
    Sanitize user input or external briefs to prevent prompt injection.
    Replaces malicious patterns with safe text.
    """
    if not text:
        return text
        
    sanitized = text
    detected = False
    
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, sanitized):
            detected = True
            sanitized = re.sub(pattern, "[REDACTED ATTEMPT]", sanitized)
            
    if detected:
        logger.warning({"event": "prompt_injection_attempt_blocked", "original": text[:100]})
        
    # Also strip weird invisible characters that might confuse the LLM
    sanitized = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', sanitized)
    
    return sanitized

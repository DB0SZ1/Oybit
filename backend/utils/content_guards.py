"""
Oybit — Content Quality Guards (GAPs 6.2–6.5, 6.7–6.8)
"""
import hashlib
import logging
import re
from collections import defaultdict
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# ── GAP 6.2: Duplicate Post Detection ──────────────────────────
_content_hashes = {}  # {hash: (account, timestamp)}

def content_fingerprint(text: str) -> str:
    """Create a normalized fingerprint of content text."""
    normalized = re.sub(r'\s+', ' ', text.lower().strip())
    normalized = re.sub(r'[^\w\s]', '', normalized)
    return hashlib.sha256(normalized.encode()).hexdigest()[:16]

def is_duplicate(text: str, account: str, window_hours: int = 72) -> bool:
    """Check if substantially similar content was posted recently."""
    fp = content_fingerprint(text)
    cutoff = datetime.utcnow() - timedelta(hours=window_hours)
    
    if fp in _content_hashes:
        prev_account, prev_time = _content_hashes[fp]
        if prev_time > cutoff:
            logger.warning({"event": "duplicate_detected", "account": account, 
                          "prev_account": prev_account, "fingerprint": fp})
            return True
    return False

def register_content(text: str, account: str):
    """Register content fingerprint after publishing."""
    fp = content_fingerprint(text)
    _content_hashes[fp] = (account, datetime.utcnow())


# ── GAP 6.3: Hook Rotation ─────────────────────────────────────
_hook_usage = defaultdict(list)  # {hook_type: [timestamps]}

def can_use_hook(hook_type: str, cooldown_posts: int = 5) -> bool:
    """Ensure the same hook type isn't used too frequently."""
    recent = _hook_usage.get(hook_type, [])
    if len(recent) >= cooldown_posts:
        cutoff = datetime.utcnow() - timedelta(days=7)
        recent_in_window = [t for t in recent if t > cutoff]
        if len(recent_in_window) >= cooldown_posts:
            return False
    return True

def record_hook_usage(hook_type: str):
    _hook_usage[hook_type].append(datetime.utcnow())


# ── GAP 6.4: Engagement Rate Normalization ──────────────────────
def normalize_engagement(likes: int, comments: int, shares: int, saves: int,
                         followers: int) -> float:
    """
    Normalize engagement to a 0-100 scale relative to follower count.
    Uses weighted formula: (likes*1 + comments*2 + shares*3 + saves*2) / followers * 100
    """
    if followers <= 0:
        return 0.0
    
    weighted = (likes * 1.0 + comments * 2.0 + shares * 3.0 + saves * 2.0)
    raw_rate = (weighted / followers) * 100
    # Cap at 100
    return min(round(raw_rate, 2), 100.0)


# ── GAP 6.5: External Amplification Detection ──────────────────
def detect_amplification(post_metrics: dict, account_avg: float) -> bool:
    """
    Detect if a post got externally amplified (viral share, influencer RT).
    Returns True if engagement is 5x+ above account average.
    """
    if account_avg <= 0:
        return False
    
    current = normalize_engagement(
        post_metrics.get("likes", 0),
        post_metrics.get("comments", 0),
        post_metrics.get("shares", 0),
        post_metrics.get("saves", 0),
        post_metrics.get("followers", 1)
    )
    
    if current > account_avg * 5:
        logger.info({"event": "amplification_detected", "score": current, "avg": account_avg})
        return True
    return False


# ── GAP 6.7: Context Window Management ─────────────────────────
def trim_context(text: str, max_tokens: int = 4000, chars_per_token: float = 4.0) -> str:
    """Trim text to fit within token budget, preserving recent content."""
    max_chars = int(max_tokens * chars_per_token)
    if len(text) <= max_chars:
        return text
    # Keep the last N characters (most recent = most relevant)
    return "...[truncated]...\n\n" + text[-max_chars:]


# ── GAP 6.8: Prompt Injection Sanitization ──────────────────────
INJECTION_PATTERNS = [
    r'ignore\s+(previous|all|above)\s+instructions',
    r'you\s+are\s+now\s+',
    r'system\s*:\s*',
    r'<\|im_start\|>',
    r'<\|im_end\|>',
    r'```system',
    r'ADMIN\s*MODE',
    r'jailbreak',
    r'DAN\s+mode',
]

def sanitize_input(text: str) -> str:
    """Remove potential prompt injection patterns from user-supplied content."""
    sanitized = text
    for pattern in INJECTION_PATTERNS:
        sanitized = re.sub(pattern, '[FILTERED]', sanitized, flags=re.IGNORECASE)
    return sanitized

def is_safe_input(text: str) -> bool:
    """Check if input contains prompt injection attempts."""
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            logger.warning({"event": "prompt_injection_detected", "pattern": pattern})
            return False
    return True

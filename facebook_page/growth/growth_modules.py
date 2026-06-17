"""
Oybit — Growth Modules (GAPS_FINAL GAPs 2.1–2.3)
Follow strategy, saved reply templates, gross follows tracking.
"""
import logging
import json
import os
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

# ── GAP 2.1: Follow Strategy Module ───────────────────────────
class FollowStrategy:
    """Manages follow/unfollow targets for organic growth."""
    
    TARGETS_FILE = Path(os.getenv("FOLLOW_TARGETS_PATH", "/data/follow_targets.json"))
    
    def __init__(self):
        self.targets = self._load_targets()
    
    def _load_targets(self) -> list[dict]:
        if self.TARGETS_FILE.exists():
            return json.loads(self.TARGETS_FILE.read_text('utf-8'))
        return []
    
    def _save_targets(self):
        self.TARGETS_FILE.parent.mkdir(parents=True, exist_ok=True)
        self.TARGETS_FILE.write_text(json.dumps(self.targets, indent=2), encoding='utf-8')
    
    def add_target(self, platform: str, user_id: str, username: str, reason: str = ""):
        self.targets.append({
            "platform": platform,
            "user_id": user_id,
            "username": username,
            "reason": reason,
            "added_at": datetime.utcnow().isoformat() + "Z",
            "followed": False,
            "follow_date": None
        })
        self._save_targets()
    
    def get_unfollowed_targets(self, platform: str = None) -> list[dict]:
        targets = [t for t in self.targets if not t.get("followed")]
        if platform:
            targets = [t for t in targets if t["platform"] == platform]
        return targets


# ── GAP 2.2: Saved Reply Templates ────────────────────────────
REPLY_TEMPLATES = {
    "thank_you": "Thank you for your kind words! Really appreciate the support 🙏",
    "question_redirect": "Great question! I actually covered this in detail — check out my recent post on {topic}.",
    "collaboration": "Love your work! Would be great to connect and explore collaboration opportunities.",
    "value_add": "That's a great point! I'd add that {insight} — what do you think?",
    "engagement": "100% agree with this. In my experience, {experience}.",
}

def get_reply_template(template_key: str, variables: dict = None) -> str:
    """Get a saved reply template with variable substitution."""
    template = REPLY_TEMPLATES.get(template_key, "")
    if variables and template:
        for key, value in variables.items():
            template = template.replace(f"{{{key}}}", str(value))
    return template


# ── GAP 2.3: Gross Follows Tracking ───────────────────────────
FOLLOWS_LOG = Path(os.getenv("FOLLOWS_LOG_PATH", "/data/follows_log.jsonl"))

def log_follow_change(platform: str, account: str, followers_count: int, 
                       follows_count: int, unfollows_count: int = 0):
    """Log daily follow/unfollow metrics."""
    FOLLOWS_LOG.parent.mkdir(parents=True, exist_ok=True)
    
    entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "platform": platform,
        "account": account,
        "followers_count": followers_count,
        "follows_count": follows_count,
        "unfollows_count": unfollows_count,
        "net_change": follows_count - unfollows_count
    }
    
    with open(FOLLOWS_LOG, 'a', encoding='utf-8') as f:
        f.write(json.dumps(entry) + '\n')

def get_follow_trend(platform: str, days: int = 30) -> list[dict]:
    """Get follow trend data for charting."""
    if not FOLLOWS_LOG.exists():
        return []
    
    entries = []
    with open(FOLLOWS_LOG, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            entry = json.loads(line)
            if entry.get("platform") == platform:
                entries.append(entry)
    
    return entries[-days:]

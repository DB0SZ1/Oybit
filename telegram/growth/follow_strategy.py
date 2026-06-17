"""
Follow Strategy — Manages follow/unfollow actions for audience growth.
Disabled by default (FOLLOW_STRATEGY_ENABLED=false).
Uses human-like timing to avoid platform detection.
"""

import random
import time
from datetime import datetime, timedelta
from config import FOLLOW_STRATEGY_ENABLED, MAX_FOLLOWS_PER_DAY
from logger import get_logger

logger = get_logger("growth.follow_strategy")

# Bot detection heuristics
BOT_INDICATORS = [
    "follow for follow", "f4f", "l4l", "like for like",
    "💰 make money", "🔥 dm me", "free followers",
    "crypto", "forex", "binary options",
]


class FollowManager:
    """
    Manages follow/unfollow cycles for audience growth.

    Rules:
    - Max follows per day controlled by MAX_FOLLOWS_PER_DAY (default: 3)
    - Human-like random delays between actions (30s-120s)
    - Never follow bot accounts (detected by bio keywords)
    - Unfollow non-reciprocators after 7 days
    - Track all actions for analytics
    """

    def __init__(self, db_session=None):
        self.db = db_session
        self.follows_today = 0
        self.max_daily = MAX_FOLLOWS_PER_DAY

    def is_enabled(self) -> bool:
        return FOLLOW_STRATEGY_ENABLED

    def is_likely_bot(self, profile: dict) -> bool:
        """Check if a profile looks like a bot."""
        bio = (profile.get("bio") or "").lower()
        username = (profile.get("username") or "").lower()

        # Check bio for spam indicators
        if any(indicator in bio for indicator in BOT_INDICATORS):
            return True

        # Check for suspicious follower/following ratios
        followers = profile.get("followers_count", 0)
        following = profile.get("following_count", 0)
        if following > 5000 and followers < 100:
            return True

        # Check for default profile picture
        if profile.get("is_default_avatar", False):
            return True

        return False

    def find_targets(
        self,
        platform: str,
        niche_keywords: list = None,
        source: str = "hashtag",
        limit: int = 10,
    ) -> list:
        """
        Find potential follow targets from a specific source.

        Args:
            platform: instagram_personal, linkedin, etc.
            niche_keywords: keywords to search for relevant accounts
            source: hashtag, similar_accounts, commenters, engagers
            limit: max targets to return

        Returns:
            list of target profile dicts
        """
        if not self.is_enabled():
            logger.info("Follow strategy disabled")
            return []

        if niche_keywords is None:
            niche_keywords = ["buildinpublic", "indiehacker", "africantech", "devtools"]

        # This would integrate with platform APIs — returning structure for now
        logger.info("Finding follow targets", extra={
            "platform": platform,
            "source": source,
            "keywords": niche_keywords[:3],
        })

        return []

    def execute_follow(self, platform: str, target_id: str, target_username: str) -> dict:
        """
        Execute a follow action with human-like timing.

        Args:
            platform: target platform
            target_id: platform user ID
            target_username: display username

        Returns:
            dict with success status and follow record
        """
        if not self.is_enabled():
            return {"success": False, "reason": "Follow strategy disabled"}

        if self.follows_today >= self.max_daily:
            return {"success": False, "reason": f"Daily limit ({self.max_daily}) reached"}

        # Human-like delay
        delay = random.uniform(30, 120)
        logger.info("Follow action pending", extra={
            "target": target_username,
            "delay_seconds": round(delay, 1),
        })
        time.sleep(delay)

        # Execute the actual follow via platform API
        # This would call the appropriate publisher's follow method
        self.follows_today += 1

        record = {
            "platform": platform,
            "target_id": target_id,
            "target_username": target_username,
            "followed_at": datetime.utcnow().isoformat(),
            "status": "followed",
        }

        logger.info("Follow executed", extra={"target": target_username, "today_total": self.follows_today})
        return {"success": True, "record": record}

    def check_reciprocity(self, follow_records: list, grace_days: int = 7) -> list:
        """
        Check which followed accounts haven't followed back within grace period.

        Args:
            follow_records: list of follow records from DB
            grace_days: days to wait before considering non-reciprocal

        Returns:
            list of accounts eligible for unfollow
        """
        cutoff = datetime.utcnow() - timedelta(days=grace_days)
        unfollow_candidates = []

        for record in follow_records:
            followed_at = record.get("followed_at")
            if isinstance(followed_at, str):
                followed_at = datetime.fromisoformat(followed_at)

            if followed_at < cutoff and not record.get("reciprocated", False):
                unfollow_candidates.append(record)

        logger.info("Reciprocity check", extra={
            "checked": len(follow_records),
            "unfollow_candidates": len(unfollow_candidates),
        })
        return unfollow_candidates

    def execute_unfollow(self, platform: str, target_id: str, target_username: str) -> dict:
        """Execute an unfollow with human-like timing."""
        delay = random.uniform(30, 90)
        time.sleep(delay)

        logger.info("Unfollow executed", extra={"target": target_username})
        return {"success": True, "unfollowed": target_username}

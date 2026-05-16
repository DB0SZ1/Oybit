"""
Rate Limit Budget Manager — Manages API call budgets per platform.
Meta's rate limits are per-app (shared across IG Personal + IG Brand + Facebook).
Reserves publish capacity to prevent analytics polling from starving publishing.
"""

import time
from datetime import datetime
from backend.logger import get_logger

logger = get_logger("api.rate_limit_manager")

PLATFORM_BUDGETS = {
    "meta": {
        "calls_per_hour": 200,
        "publish_reserve": 50,    # Always keep 50 calls reserved for publishing
        "analytics_ceiling": 150,  # Analytics can use max 150/hour
    },
    "linkedin": {
        "calls_per_hour": 100,
        "publish_reserve": 20,
        "analytics_ceiling": 80,
    },
    "reddit": {
        "calls_per_hour": 60,
        "publish_reserve": 10,
        "analytics_ceiling": 50,
    },
    "youtube": {
        "calls_per_hour": 50,
        "publish_reserve": 10,
        "analytics_ceiling": 40,
    },
    "pinterest": {
        "calls_per_hour": 50,
        "publish_reserve": 10,
        "analytics_ceiling": 40,
    },
}


class RateLimitManager:
    """
    Tracks API calls per platform per hour window.
    Enforces publish-reserved capacity and analytics ceilings.
    """

    def __init__(self):
        self._counters = {}  # platform -> {"count": int, "window_start": float}

    def _get_window(self, platform: str) -> dict:
        """Get or create the current hour window for a platform."""
        now = time.time()
        window = self._counters.get(platform)

        if window is None or (now - window["window_start"]) >= 3600:
            # New window
            self._counters[platform] = {"count": 0, "window_start": now}

        return self._counters[platform]

    def can_make_call(self, platform: str, call_type: str = "analytics") -> bool:
        """
        Check if an API call is allowed within the budget.

        Args:
            platform: meta, linkedin, reddit, etc.
            call_type: 'publish' or 'analytics'

        Returns:
            True if the call is within budget
        """
        budget = PLATFORM_BUDGETS.get(platform)
        if not budget:
            return True  # Unknown platform — no limits

        window = self._get_window(platform)
        current_count = window["count"]

        if call_type == "publish":
            # Publishing always allowed until total ceiling hit
            allowed = current_count < budget["calls_per_hour"]
        elif call_type == "analytics":
            # Analytics backed off when near publish reserve
            remaining = budget["calls_per_hour"] - current_count
            allowed = remaining > budget["publish_reserve"]
        else:
            allowed = current_count < budget["calls_per_hour"]

        if not allowed:
            logger.warning("Rate limit exceeded", extra={
                "platform": platform,
                "call_type": call_type,
                "current_count": current_count,
                "budget": budget["calls_per_hour"],
            })

        return allowed

    def record_call(self, platform: str):
        """Record that an API call was made."""
        window = self._get_window(platform)
        window["count"] += 1

    def get_remaining(self, platform: str) -> dict:
        """Get remaining API call budget for a platform."""
        budget = PLATFORM_BUDGETS.get(platform, {"calls_per_hour": 0, "publish_reserve": 0})
        window = self._get_window(platform)
        current = window["count"]
        total = budget["calls_per_hour"]

        return {
            "platform": platform,
            "total_budget": total,
            "used": current,
            "remaining": max(0, total - current),
            "publish_remaining": max(0, total - current),
            "analytics_remaining": max(0, total - current - budget["publish_reserve"]),
        }

    def get_all_budgets(self) -> dict:
        """Get remaining budgets for all platforms."""
        return {p: self.get_remaining(p) for p in PLATFORM_BUDGETS}


# Global singleton
rate_limiter = RateLimitManager()

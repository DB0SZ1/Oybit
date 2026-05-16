"""
Oybit — Rate Limit Budget Manager (GAP 5.3)
Tracks API call budgets per platform and blocks calls when near the limit.
"""
import time
import logging
import threading
from collections import defaultdict

logger = logging.getLogger(__name__)

class RateLimitBudget:
    """Thread-safe rate limit tracker for all platform APIs."""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._init()
        return cls._instance
    
    def _init(self):
        # Platform limits: {platform: {calls_per_hour, calls_per_day}}
        self.limits = {
            "meta": {"per_hour": 200, "per_day": 4800},
            "linkedin": {"per_hour": 100, "per_day": 1000},
            "reddit": {"per_minute": 60, "per_day": 1000},
            "pinterest": {"per_hour": 1000, "per_day": 10000},
            "openrouter": {"per_minute": 20, "per_day": 200},
            "pollinations": {"per_hour": 60, "per_day": 500},
        }
        # Sliding window: {platform: [timestamps]}
        self._calls = defaultdict(list)
        self._lock_internal = threading.Lock()
    
    def can_call(self, platform: str) -> bool:
        """Check if we're within budget for this platform."""
        limits = self.limits.get(platform)
        if not limits:
            return True  # No limits configured = allow
        
        now = time.time()
        with self._lock_internal:
            calls = self._calls[platform]
            # Prune old entries
            calls[:] = [t for t in calls if now - t < 86400]  # Keep 24h
            
            # Check per_minute
            if "per_minute" in limits:
                recent_minute = sum(1 for t in calls if now - t < 60)
                if recent_minute >= limits["per_minute"]:
                    logger.warning({"event": "rate_limit_blocked", "platform": platform, "window": "minute"})
                    return False
            
            # Check per_hour
            if "per_hour" in limits:
                recent_hour = sum(1 for t in calls if now - t < 3600)
                if recent_hour >= limits["per_hour"]:
                    logger.warning({"event": "rate_limit_blocked", "platform": platform, "window": "hour"})
                    return False
            
            # Check per_day
            if "per_day" in limits:
                if len(calls) >= limits["per_day"]:
                    logger.warning({"event": "rate_limit_blocked", "platform": platform, "window": "day"})
                    return False
        
        return True
    
    def record_call(self, platform: str):
        """Record an API call for budget tracking."""
        with self._lock_internal:
            self._calls[platform].append(time.time())
    
    def get_remaining(self, platform: str) -> dict:
        """Get remaining budget for a platform."""
        limits = self.limits.get(platform, {})
        now = time.time()
        
        with self._lock_internal:
            calls = self._calls[platform]
            calls[:] = [t for t in calls if now - t < 86400]
            
            result = {}
            if "per_minute" in limits:
                recent = sum(1 for t in calls if now - t < 60)
                result["minute"] = limits["per_minute"] - recent
            if "per_hour" in limits:
                recent = sum(1 for t in calls if now - t < 3600)
                result["hour"] = limits["per_hour"] - recent
            if "per_day" in limits:
                result["day"] = limits["per_day"] - len(calls)
        
        return result

# Singleton instance
budget = RateLimitBudget()

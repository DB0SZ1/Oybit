"""
Oybit — API Improvements (GAPs 14.1–14.4, 16.1)
Pydantic schemas, CORS, async gate endpoint, API versioning, SSRF protection.
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum

# ── GAP 14.1: Pydantic Schemas ─────────────────────────────────

class PostTypeEnum(str, Enum):
    text = "text"
    image = "image"
    carousel = "carousel"
    video = "video"
    reel = "reel"
    story = "story"
    poll = "poll"

class ContentGenerateRequest(BaseModel):
    topic_brief: str = Field(..., min_length=5, max_length=500)
    platform: str = Field(..., pattern="^(instagram_personal|instagram_brand|facebook|linkedin|reddit|pinterest|youtube|bluesky)$")
    format_type: str = Field(default="text")
    account: Optional[str] = None
    dry_run: bool = False

class ContentGenerateResponse(BaseModel):
    variants: dict[str, str]
    image_path: Optional[str] = None
    generated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")

class PublishRequest(BaseModel):
    post_id: int
    account: str
    dry_run: bool = False

class PublishResponse(BaseModel):
    success: bool
    platform_post_id: Optional[str] = None
    error: Optional[str] = None

class ScheduleRequest(BaseModel):
    post_id: int
    account: str
    scheduled_at: datetime

class GateRequest(BaseModel):
    post_id: int
    
class GateResponse(BaseModel):
    decision: str  # PASS, HOLD, KILL
    source: str    # mirofish, score_fallback
    confidence: float
    warnings: list[str] = []

class EventIngestRequest(BaseModel):
    event_text: str = Field(..., min_length=3, max_length=1000)
    event_type: str = Field(default="general")
    source: str = Field(default="manual")

class WaitlistEntryCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    email: str = Field(..., min_length=5, max_length=254)
    why_interested: Optional[str] = Field(default=None, max_length=1000)
    source: Optional[str] = Field(default="website", max_length=50)

class FeedbackCreate(BaseModel):
    post_id: int
    rating: int = Field(..., ge=1, le=10)
    reasoning: Optional[str] = Field(default=None, max_length=1000)
    platform: Optional[str] = None

class NyvoraWebhookPayload(BaseModel):
    event: str = Field(..., min_length=1, max_length=100)
    project: str = Field(..., min_length=1, max_length=200)
    data: Optional[dict] = None
    timestamp: Optional[str] = None

class EventCreate(BaseModel):
    event_text: str = Field(..., min_length=3, max_length=1000)
    event_type: str = Field(default="general", max_length=50)
    source: str = Field(default="manual", max_length=50)

class AnalyticsSummary(BaseModel):
    account: str
    total_posts: int
    avg_engagement: float
    top_hook_types: list[str]
    period: str

# ── GAP 14.4: API Version Constants ───────────────────────────
API_VERSION = "v1"
META_API_VERSION = "v21.0"
LINKEDIN_API_VERSION = "v2"
PINTEREST_API_VERSION = "v5"
YOUTUBE_API_VERSION = "v3"


# ── GAP 16.1: SSRF Protection ─────────────────────────────────
import ipaddress
from urllib.parse import urlparse

BLOCKED_HOSTS = {"localhost", "127.0.0.1", "0.0.0.0", "169.254.169.254", "metadata.google.internal"}

def is_safe_url(url: str) -> bool:
    """Validate URL is not pointing to internal/private resources (SSRF protection)."""
    try:
        parsed = urlparse(url)
        host = parsed.hostname
        
        if not host:
            return False
        
        # Block known internal hosts
        if host in BLOCKED_HOSTS:
            return False
        
        # Block private IP ranges
        try:
            ip = ipaddress.ip_address(host)
            if ip.is_private or ip.is_loopback or ip.is_link_local:
                return False
        except ValueError:
            pass  # Not an IP, it's a hostname — that's fine
        
        # Block non-HTTP(S) schemes
        if parsed.scheme not in ("http", "https"):
            return False
        
        return True
    except Exception:
        return False

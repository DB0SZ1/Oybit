# GAPS_AND_FIXES.md — Oybit Complete Gap Remediation
# Read this after AGENTS.md and TESTS.md.
# Every gap identified. Every fix specified. Every search needed.
# This is what makes Oybit a real system, not a demo.

---

## HOW TO USE THIS FILE

Both agents read this entirely before writing any new code or modifying existing code.
Every section has: the gap, the fix, what to build, what to search, what library to use.
Gaps are organized by category. Some gaps require new files. Some require modifying existing ones.
Every gap here overrides anything in AGENTS.md if there is a conflict.

---

---

# SECTION 1 — ENVIRONMENT AND SHELL

## GAP 1.1 — PowerShell Breaks Everything

**Problem:** Antigravity IDE on Windows defaults to PowerShell. Python subprocess calls, ffmpeg path resolution, Remotion renders, and file path handling all behave differently in PowerShell vs bash. Unicode characters in PowerShell cause encoding errors. Emoji in print statements crash the terminal.

**Fix:**
- All shell commands use bash explicitly
- All subprocess calls use `shell=False` with explicit argument lists (never string commands)
- All file paths use `pathlib.Path` not string concatenation
- All print/log statements use ASCII only — no emoji, no unicode symbols
- Set `PYTHONIOENCODING=utf-8` in all worker startup scripts

**What to build:**
```python
# backend/utils/shell.py
import subprocess
from pathlib import Path

def run_command(args: list, cwd: Path = None, timeout: int = 300) -> tuple[int, str, str]:
    """
    Safe subprocess wrapper. Never use shell=True.
    Returns (returncode, stdout, stderr)
    """
    result = subprocess.run(
        args,
        capture_output=True,
        text=True,
        cwd=str(cwd) if cwd else None,
        timeout=timeout,
        shell=False,  # NEVER True
        encoding='utf-8',
        errors='replace'
    )
    return result.returncode, result.stdout, result.stderr
```

**In every worker file add at top:**
```python
import os
import sys
os.environ['PYTHONIOENCODING'] = 'utf-8'
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
```

---

## GAP 1.2 — Nixpacks Missing System Dependencies

**Problem:** Playwright and Remotion both require system-level Chrome/Chromium dependencies not present by default on Railway or Render. Without them, carousel and video rendering fail with cryptic "browser not found" errors.

**Fix:** Create `nixpacks.toml` at project root:

```toml
[phases.setup]
nixPkgs = [
  "nodejs_20",
  "chromium",
  "nss",
  "nspr",
  "atk",
  "cups",
  "libdrm",
  "dbus",
  "xorg.libX11",
  "xorg.libXcomposite",
  "xorg.libXdamage",
  "xorg.libXext",
  "xorg.libXfixes",
  "xorg.libXrandr",
  "mesa",
  "expat",
  "xorg.libxcb",
  "libxkbcommon",
  "pango",
  "cairo",
  "alsa-lib",
  "ffmpeg"
]

[phases.install]
cmds = [
  "pip install -r requirements.txt",
  "playwright install chromium --with-deps",
  "cd render_engine/templates/video && npm install"
]

[start]
cmd = "uvicorn backend.main:app --host 0.0.0.0 --port $PORT"
```

**Also create `render.yaml` for Render compatibility:**
```yaml
services:
  - type: web
    name: oybit-api
    env: python
    buildCommand: "pip install -r requirements.txt && playwright install chromium --with-deps && cd render_engine/templates/video && npm install"
    startCommand: "uvicorn backend.main:app --host 0.0.0.0 --port $PORT"
    healthCheckPath: /health
    envVars:
      - key: PYTHONIOENCODING
        value: utf-8

  - type: worker
    name: oybit-scheduler
    env: python
    startCommand: "python workers/scheduler_worker.py"

  - type: worker
    name: oybit-mirofish
    env: python
    startCommand: "python workers/mirofish_worker.py"

  - type: worker
    name: oybit-analytics
    env: python
    startCommand: "python workers/analytics_worker.py"

  - type: worker
    name: oybit-feedback
    env: python
    startCommand: "python workers/feedback_worker.py"

  - type: worker
    name: oybit-trends
    env: python
    startCommand: "python workers/trend_worker.py"

  - type: worker
    name: oybit-token-refresher
    env: python
    startCommand: "python workers/token_refresher.py"

  - type: worker
    name: oybit-keepalive
    env: python
    startCommand: "python workers/keepalive_worker.py"
```

---

## GAP 1.3 — Render Anti-Sleep

**Problem:** Render free tier sleeps after 15 minutes of inactivity. The API goes to sleep, first request after sleep takes 30+ seconds, scheduled posts miss their window.

**Fix:** Build `workers/keepalive_worker.py`:
```python
import time
import httpx
import os
import logging

logger = logging.getLogger(__name__)

API_URL = os.getenv("API_URL", "http://localhost:8000")
PING_INTERVAL = int(os.getenv("KEEPALIVE_INTERVAL", "600"))  # 10 minutes

def ping():
    try:
        response = httpx.get(f"{API_URL}/health", timeout=10)
        if response.status_code == 200:
            logger.info({"event": "keepalive_ping", "status": "ok"})
        else:
            logger.warning({"event": "keepalive_ping", "status": response.status_code})
    except Exception as e:
        logger.error({"event": "keepalive_ping", "error": str(e)})

if __name__ == "__main__":
    logger.info({"event": "keepalive_start", "interval": PING_INTERVAL})
    while True:
        ping()
        time.sleep(PING_INTERVAL)
```

**The /health endpoint must be deep — not shallow:**
```python
# backend/api/health.py
@router.get("/health")
async def health_check(db: Session = Depends(get_db)):
    checks = {}

    # Check DB
    try:
        db.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as e:
        checks["database"] = f"FAIL: {str(e)}"

    # Check Redis
    try:
        redis_client.ping()
        checks["redis"] = "ok"
    except Exception as e:
        checks["redis"] = f"FAIL: {str(e)}"

    # Check persona.md volume mount
    persona_path = Path(os.getenv("PERSONA_PATH", "/data/personas/ahmad/persona.md"))
    checks["persona_volume"] = "ok" if persona_path.parent.exists() else "FAIL: volume not mounted"

    # Check queue.db
    queue_path = Path(os.getenv("QUEUE_PATH", "/data/queue.db"))
    checks["queue_volume"] = "ok" if queue_path.parent.exists() else "FAIL: volume not mounted"

    # Worker heartbeats
    # Check each worker's last_run from DB
    for worker in ["mirofish", "analytics", "feedback", "trend", "scheduler"]:
        last_run = get_worker_last_run(db, worker)
        if last_run:
            age_hours = (datetime.utcnow() - last_run).total_seconds() / 3600
            checks[f"worker_{worker}"] = "ok" if age_hours < 26 else f"WARN: last ran {age_hours:.1f}h ago"
        else:
            checks[f"worker_{worker}"] = "never_run"

    all_ok = all(v == "ok" or v.startswith("ok") or v == "never_run" for v in checks.values())
    status_code = 200 if all_ok else 503

    return JSONResponse(content={"status": "ok" if all_ok else "degraded", "checks": checks}, status_code=status_code)
```

---

---

# SECTION 2 — DATABASE AND MODELS

## GAP 2.1 — Single Base Declaration

**Problem:** Both agents created separate `Base = declarative_base()` in their model files. SQLAlchemy requires exactly one Base shared across all models.

**Fix:** Create `backend/db/base.py`:
```python
from sqlalchemy.orm import declarative_base
Base = declarative_base()
```

Every model file imports from here:
```python
from backend.db.base import Base
```

Never declare `Base = declarative_base()` anywhere else in the codebase.

---

## GAP 2.2 — SQLite WAL Mode

**Problem:** Default SQLite journal mode causes `database is locked` errors when scheduler_worker and analytics_worker access queue.db simultaneously.

**Fix:** In `backend/scheduler_worker/queue.py`, set WAL mode on every connection:
```python
import sqlite3

def get_connection():
    conn = sqlite3.connect(QUEUE_PATH, check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA busy_timeout=5000")  # wait 5s before giving up on lock
    return conn
```

---

## GAP 2.3 — PostgreSQL Connection Pooling

**Fix:** In `backend/db/session.py`:
```python
engine = create_engine(
    DATABASE_URL,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,       # test connections before use
    pool_recycle=3600,         # recycle connections every hour
    connect_args={"connect_timeout": 10}
)
```

---

## GAP 2.4 — Atomic Writes for persona.md

**Problem:** If power/process dies mid-write, persona.md is corrupted. Half-written file = broken system.

**Fix:** All writes to persona.md must be atomic:
```python
import tempfile
import os
from pathlib import Path

def atomic_write(path: Path, content: str):
    """Write to temp file then rename — atomic on POSIX systems."""
    dir_path = path.parent
    with tempfile.NamedTemporaryFile(
        mode='w',
        dir=dir_path,
        delete=False,
        suffix='.tmp',
        encoding='utf-8'
    ) as tmp:
        tmp.write(content)
        tmp_path = tmp.name
    os.replace(tmp_path, path)  # atomic rename
```

---

## GAP 2.5 — simulation_log.md File Locking

**Problem:** If calibration.py and feedback_worker.py both append to simulation_log.md simultaneously, the file can be corrupted.

**Fix:**
```python
import fcntl  # Unix only — works on Railway/Render

def append_to_simulation_log(log_path: Path, entry: str):
    with open(log_path, 'a', encoding='utf-8') as f:
        fcntl.flock(f, fcntl.LOCK_EX)  # exclusive lock
        try:
            f.write(entry + '\n')
            f.flush()
            os.fsync(f.fileno())
        finally:
            fcntl.flock(f, fcntl.LOCK_UN)  # always release
```

---

## GAP 2.6 — Missing Fields in Post and PatternDB Models

**Add to Post model:**
```python
post_type = Column(String)  # text_only|image_only|text_with_image|text_with_video|carousel|reel|story
followers_at_post_time = Column(Integer)  # CRITICAL for engagement rate normalization
normalized_engagement_score = Column(Float)  # score / followers_at_post_time
is_externally_amplified = Column(Boolean, default=False)
post_publish_verified = Column(Boolean, default=False)  # confirmed still live 15min after
is_moderated = Column(Boolean, default=False)  # detected as removed by platform
sub_topic = Column(String)   # finer-grained than topic_pillar
emotional_tone = Column(String)  # consequence|insight|contradiction|celebration|frustration
audience_segment = Column(String)  # nigerian_dev|indie_hacker|linkedin_professional|general
```

**Add to PatternDB model:**
```python
sub_topic = Column(String)
emotional_tone = Column(String)
audience_segment = Column(String)
avg_normalized_score = Column(Float)  # normalized by followers_at_post_time
```

---

## GAP 2.7 — Data Archiving Strategy

**Build `workers/archive_worker.py`** (runs monthly):
```python
# Archive PostAnalytics older than 6 months to archive table
# Compress MiroFishRun JSON older than 30 days
# Warn if simulation_log.md > 10MB
# Delete render temp files older than 24h
```

**Add `WorkerHeartbeat` model:**
```python
class WorkerHeartbeat(Base):
    __tablename__ = "worker_heartbeats"
    id = Column(Integer, primary_key=True)
    worker_name = Column(String, unique=True)
    last_run = Column(DateTime)
    last_status = Column(String)  # ok|failed|running
    last_error = Column(Text)
```

Every worker writes heartbeat at start and end of each run.

---

---

# SECTION 3 — ERROR HANDLING STANDARDS

## GAP 3.1 — Meta Graph API Error Handling

**Problem:** Meta returns HTTP 200 with error in body when token expires. Standard HTTP error handling misses this entirely.

**Fix — in every Meta API call:**
```python
def check_meta_response(response: httpx.Response, context: str) -> dict:
    data = response.json()

    # Meta error in 200 response
    if "error" in data:
        error = data["error"]
        code = error.get("code")
        message = error.get("message", "Unknown Meta error")

        if code == 190:  # Token expired/invalid
            raise MetaTokenExpiredError(f"Token expired for {context}: {message}")
        elif code == 100:  # Invalid parameter
            raise MetaInvalidParamError(f"Invalid param in {context}: {message}")
        elif code == 17:  # Rate limit
            raise MetaRateLimitError(f"Rate limited in {context}: {message}")
        elif code == 368:  # Temporarily blocked
            raise MetaBlockedError(f"Account temporarily blocked: {message}")
        else:
            raise MetaAPIError(f"Meta error {code} in {context}: {message}")

    return data
```

**Create `backend/utils/exceptions.py`** with all custom exceptions:
```python
class OybitBaseError(Exception): pass

# Meta
class MetaTokenExpiredError(OybitBaseError): pass
class MetaRateLimitError(OybitBaseError): pass
class MetaInvalidParamError(OybitBaseError): pass
class MetaBlockedError(OybitBaseError): pass
class MetaAPIError(OybitBaseError): pass
class MetaModerationError(OybitBaseError): pass

# LinkedIn
class LinkedInTokenExpiredError(OybitBaseError): pass
class LinkedInRateLimitError(OybitBaseError): pass
class LinkedInInvalidPayloadError(OybitBaseError): pass

# OpenRouter
class OpenRouterRateLimitError(OybitBaseError): pass
class OpenRouterModelUnavailableError(OybitBaseError): pass
class OpenRouterContextWindowError(OybitBaseError): pass

# MiroFish
class MiroFishSimulationError(OybitBaseError): pass
class MiroFishEmptyOutputError(OybitBaseError): pass
class GraphRAGConfigError(OybitBaseError): pass

# Rendering
class CarouselRenderError(OybitBaseError): pass
class VideoRenderError(OybitBaseError): pass
class FontNotFoundError(OybitBaseError): pass
class SlideOverflowError(OybitBaseError): pass

# Publishing
class PostAlreadyPublishedError(OybitBaseError): pass
class PostRemovedByPlatformError(OybitBaseError): pass
class PostSuppressedError(OybitBaseError): pass

# File system
class PersonaFileNotFoundError(OybitBaseError): pass
class SimulationLogCorruptedError(OybitBaseError): pass
class VolumeNotMountedError(OybitBaseError): pass
```

---

## GAP 3.2 — OpenRouter Retry with retry-after Header

```python
import time
import httpx

def call_openrouter_with_retry(payload: dict, max_retries: int = 3) -> dict:
    for attempt in range(max_retries):
        response = httpx.post(
            "https://openrouter.ai/api/v1/chat/completions",
            json=payload,
            headers=HEADERS,
            timeout=60
        )

        if response.status_code == 200:
            return response.json()

        elif response.status_code == 429:
            retry_after = int(response.headers.get("retry-after", 30))
            logger.warning({"event": "openrouter_rate_limit", "retry_after": retry_after, "attempt": attempt})
            if attempt < max_retries - 1:
                time.sleep(retry_after)
            continue

        elif response.status_code == 503:
            # OpenRouter down — try fallback provider
            logger.error({"event": "openrouter_down", "attempt": attempt})
            return call_fallback_provider(payload)

        else:
            raise OpenRouterAPIError(f"HTTP {response.status_code}: {response.text[:200]}")

    raise OpenRouterRateLimitError("Max retries exceeded")
```

**Fallback provider order:** OpenRouter → direct Groq API → direct Anthropic API

---

## GAP 3.3 — Pollinations Content-Type Check

```python
def download_pollinations_image(url: str, output_path: Path) -> Path:
    response = httpx.get(url, timeout=30, follow_redirects=True)

    # Check it's actually an image, not an HTML error page
    content_type = response.headers.get("content-type", "")
    if "image" not in content_type:
        raise ValueError(f"Pollinations returned non-image content: {content_type}")

    if len(response.content) < 1000:  # too small to be a real image
        raise ValueError(f"Pollinations returned suspiciously small file: {len(response.content)} bytes")

    with open(output_path, "wb") as f:
        f.write(response.content)

    return output_path
```

---

## GAP 3.4 — Render Output Verification

After every render, verify output exists and is valid:

```python
def verify_render_output(output_path: Path, min_size_bytes: int = 10000):
    if not output_path.exists():
        raise CarouselRenderError(f"Render output not found at {output_path}")
    if output_path.stat().st_size < min_size_bytes:
        raise CarouselRenderError(f"Render output too small: {output_path.stat().st_size} bytes")
    return True

def verify_video_output(output_path: Path):
    if not output_path.exists():
        raise VideoRenderError(f"Video output not found at {output_path}")
    # Verify with ffprobe
    rc, stdout, stderr = run_command(["ffprobe", "-v", "error", "-show_entries",
        "format=duration", "-of", "json", str(output_path)])
    if rc != 0:
        raise VideoRenderError(f"ffprobe validation failed: {stderr}")
```

---

## GAP 3.5 — Idempotency on Publish

**Problem:** Scheduler could fire twice for same job (crash + restart scenario). Same post goes out twice.

```python
def publish_with_idempotency_check(post_id: int, account: str, db: Session):
    # Check if already published
    post = db.query(Post).filter_by(id=post_id).first()
    if post.status == "published":
        logger.warning({"event": "duplicate_publish_prevented", "post_id": post_id})
        raise PostAlreadyPublishedError(f"Post {post_id} already published")

    # Acquire DB-level lock
    db.execute(
        text("SELECT pg_advisory_xact_lock(:lock_key)"),
        {"lock_key": post_id}
    )

    # Re-check after lock
    db.refresh(post)
    if post.status == "published":
        raise PostAlreadyPublishedError(f"Post {post_id} already published (race condition caught)")

    # Proceed with publish
    ...
```

---

---

# SECTION 4 — LOGGING STANDARDS

## GAP 4.1 — Structured JSON Logging

**Build `backend/utils/logger.py`** — used by every module:

```python
import logging
import json
import os
from datetime import datetime

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "message": record.getMessage(),
        }
        # If context dict was passed, merge it
        if hasattr(record, 'context') and isinstance(record.context, dict):
            # Mask sensitive fields
            safe_context = mask_sensitive(record.context)
            log_entry.update(safe_context)
        return json.dumps(log_entry, ensure_ascii=True)

SENSITIVE_KEYS = {
    "access_token", "refresh_token", "token", "secret", "password",
    "api_key", "client_secret", "app_secret", "persona_content"
}

def mask_sensitive(data: dict) -> dict:
    result = {}
    for k, v in data.items():
        if any(sensitive in k.lower() for sensitive in SENSITIVE_KEYS):
            result[k] = "***MASKED***"
        elif isinstance(v, dict):
            result[k] = mask_sensitive(v)
        else:
            result[k] = v
    return result

def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(JSONFormatter())
        logger.addHandler(handler)
        logger.setLevel(os.getenv("LOG_LEVEL", "INFO"))
    return logger
```

**Usage in every module:**
```python
from backend.utils.logger import get_logger
logger = get_logger(__name__)

# Good log call:
logger.info("Platform API call", extra={"context": {
    "event": "instagram_publish",
    "account": "instagram_personal",
    "post_id": 123,
    "response_status": 200,
    "response_time_ms": 450
}})

# Error log:
logger.error("Publish failed", extra={"context": {
    "event": "publish_failed",
    "post_id": 123,
    "account": account,
    "error_type": type(e).__name__,
    "error_message": str(e)
}})
```

---

## GAP 4.2 — Decision Audit Log

**Build `backend/db/audit.py`:**

```python
class AuditLog(Base):
    __tablename__ = "audit_log"
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    event_type = Column(String)  # post_approved|post_rejected|persona_updated|gate_failed|etc
    entity_type = Column(String)  # post|persona|pattern|worker
    entity_id = Column(String)
    decision = Column(String)
    reason = Column(Text)
    context_json = Column(Text)  # full context as JSON string
    worker_or_module = Column(String)

def audit(db: Session, event_type: str, entity_type: str, entity_id: str,
          decision: str, reason: str, context: dict, source: str):
    entry = AuditLog(
        event_type=event_type,
        entity_type=entity_type,
        entity_id=str(entity_id),
        decision=decision,
        reason=reason,
        context_json=json.dumps(context, ensure_ascii=True),
        worker_or_module=source
    )
    db.add(entry)
    db.commit()
```

**Every significant decision must call `audit()`:**
- Post scored and selected
- Post rejected by guardian
- Gate passes or fails
- Persona.md updated
- Post published successfully
- Post failed to publish
- Token refreshed
- Pattern detected
- Worker started/stopped
- MiroFish run completed

---

---

# SECTION 5 — PUBLISHING LAYER

## GAP 5.1 — Post Type Enum and Payload Builders

**Problem:** Every platform requires completely different API payload structure depending on whether the post is text only, image only, text+image, text+video, carousel, reel, or story. This is not handled anywhere.

**Build `backend/publishers/payload_builders/` folder with one file per platform:**

```
backend/publishers/payload_builders/
├── __init__.py
├── post_types.py          # PostType enum
├── instagram_payloads.py  # builds payloads for each Instagram post type
├── facebook_payloads.py   # builds payloads for each Facebook post type
└── linkedin_payloads.py   # builds payloads for each LinkedIn post type
```

**`post_types.py`:**
```python
from enum import Enum

class PostType(Enum):
    TEXT_ONLY = "text_only"
    IMAGE_ONLY = "image_only"
    TEXT_WITH_IMAGE = "text_with_image"
    TEXT_WITH_VIDEO = "text_with_video"
    CAROUSEL = "carousel"
    REEL = "reel"
    STORY_PHOTO = "story_photo"
    STORY_VIDEO = "story_video"
    LINKEDIN_ARTICLE = "linkedin_article"
    FACEBOOK_REEL = "facebook_reel"
```

**LinkedIn payload builder (CRITICAL — text+image is different from image-only):**
```python
def build_linkedin_payload(post_type: PostType, text: str, person_urn: str,
                            image_asset_urn: str = None, video_asset_urn: str = None) -> dict:
    base = {
        "author": person_urn,
        "lifecycleState": "PUBLISHED",
        "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"}
    }

    if post_type == PostType.TEXT_ONLY:
        base["specificContent"] = {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {"text": text},
                "shareMediaCategory": "NONE"
            }
        }

    elif post_type == PostType.TEXT_WITH_IMAGE:
        # BOTH text AND image — different from image-only
        base["specificContent"] = {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {"text": text},
                "shareMediaCategory": "IMAGE",
                "media": [{
                    "status": "READY",
                    "media": image_asset_urn
                }]
            }
        }

    elif post_type == PostType.TEXT_WITH_VIDEO:
        base["specificContent"] = {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {"text": text},
                "shareMediaCategory": "VIDEO",
                "media": [{
                    "status": "READY",
                    "media": video_asset_urn
                }]
            }
        }

    return base
```

**Facebook text+image payload (NOT the same as photo post):**
```python
def build_facebook_text_with_image(page_id: str, text: str,
                                    image_urls: list, page_token: str) -> dict:
    # Step 1: Create unpublished photo objects
    # Step 2: Attach to feed post with attached_media array
    # This is completely different from POST /{page-id}/photos
    pass

# Search: "facebook graph api attached_media feed post"
# Reference: https://developers.facebook.com/docs/graph-api/reference/page/feed/
```

---

## GAP 5.2 — Post-Publish Verification

**Build `backend/publishers/verifier.py`:**

```python
import asyncio
from datetime import datetime, timedelta

async def verify_post_exists(post_id: int, platform_post_id: str,
                              account: str, db: Session):
    """Run 15 minutes after publish to confirm post still exists."""
    await asyncio.sleep(900)  # 15 minutes

    try:
        exists = await fetch_post_from_platform(platform_post_id, account)

        if not exists:
            # Post was moderated/removed
            update_post_status(db, post_id, "moderated")
            send_alert(f"Post {post_id} was removed by {account} platform moderation")
            # CRITICAL: Do NOT feed this into learning engine as "low performer"
            mark_post_excluded_from_learning(db, post_id)

        else:
            update_post_publish_verified(db, post_id, True)

    except Exception as e:
        logger.error({"event": "post_verification_failed", "post_id": post_id, "error": str(e)})
```

**Add to scheduler_dispatcher.py** — after every successful publish:
```python
# Fire and forget verification task
asyncio.create_task(verify_post_exists(post_id, platform_post_id, account, db))
```

---

## GAP 5.3 — Rate Limit Budget Manager

**Build `backend/publishers/rate_limit_manager.py`:**

```python
import redis
from datetime import datetime

class RateLimitManager:
    """
    Meta Graph API: shared pool across all accounts on same app.
    Publishing gets priority. Analytics backs off when budget low.
    """

    LIMITS = {
        "meta_graph": {"calls_per_hour": 200, "priority_reserve": 50},
        "linkedin": {"calls_per_hour": 100, "priority_reserve": 20},
        "reddit": {"calls_per_day": 60, "priority_reserve": 10},
    }

    def can_make_call(self, platform: str, call_type: str) -> bool:
        """call_type: 'publish' | 'analytics' | 'read'"""
        current = self.get_current_usage(platform)
        limit = self.LIMITS[platform]["calls_per_hour"]
        reserve = self.LIMITS[platform]["priority_reserve"]

        if call_type == "publish":
            return current < limit  # publish uses full budget
        elif call_type == "analytics":
            return current < (limit - reserve)  # analytics backs off when near limit
        else:
            return current < (limit - reserve // 2)

    def record_call(self, platform: str):
        key = f"rate_limit:{platform}:{datetime.utcnow().strftime('%Y%m%d%H')}"
        self.redis.incr(key)
        self.redis.expire(key, 3600)
```

---

## GAP 5.4 — Reddit Anti-Detection

**In `backend/publishers/reddit.py`:**
```python
import random
import time

class RedditPublisher:
    MAX_POSTS_PER_DAY_PER_SUBREDDIT = 2
    MIN_DELAY_BETWEEN_ACTIONS = 45  # seconds minimum
    MAX_DELAY_BETWEEN_ACTIONS = 180  # randomize up to 3 minutes

    def post_with_human_timing(self, subreddit: str, title: str, text: str):
        # Random delay before posting (human-like behavior)
        delay = random.uniform(self.MIN_DELAY_BETWEEN_ACTIONS,
                               self.MAX_DELAY_BETWEEN_ACTIONS)
        time.sleep(delay)

        # Check daily post limit for this subreddit
        if self.get_today_post_count(subreddit) >= self.MAX_POSTS_PER_DAY_PER_SUBREDDIT:
            raise Exception(f"Daily post limit reached for r/{subreddit}")

        # Randomize scheduled time within ±30 minute window
        # Never post at exact :00 or :30 — too mechanical
        ...
```

---

---

# SECTION 6 — CONTENT AND GENERATION

## GAP 6.1 — Image + Text Simultaneous Generation

Content generator must know what post_type to generate for. Add to every generation call:

```python
def generate_post(brief: dict, platform: str, account: str,
                  post_type: PostType, persona_path: Path) -> GeneratedPost:
    """
    post_type determines:
    - Whether to generate image prompt alongside text
    - Character limits to enforce
    - Format instructions to include in prompt
    """
    char_limits = {
        "linkedin": {"TEXT_ONLY": 1300, "TEXT_WITH_IMAGE": 1300},
        "instagram_personal": {"CAROUSEL": 2200, "REEL": 125, "TEXT_WITH_IMAGE": 2200},
        "instagram_brand": {"CAROUSEL": 2200, "REEL": 125},
        "facebook": {"TEXT_ONLY": 63206, "TEXT_WITH_IMAGE": 63206},
    }

    limit = char_limits.get(account, {}).get(post_type.value, 1000)

    # Pass post_type and char_limit to prompt_builder
    ...
```

---

## GAP 6.2 — Duplicate Post Detection

**Build `backend/content/deduplication.py`:**

```python
from sentence_transformers import SentenceTransformer
import numpy as np

model = SentenceTransformer('all-MiniLM-L6-v2')

def is_duplicate(new_post_text: str, recent_posts: list[str],
                 threshold: float = 0.85) -> bool:
    """
    Semantic similarity check against last 30 published posts.
    Returns True if too similar to existing content.
    """
    if not recent_posts:
        return False

    new_embedding = model.encode([new_post_text])
    existing_embeddings = model.encode(recent_posts)

    similarities = np.dot(new_embedding, existing_embeddings.T)[0]
    max_similarity = float(np.max(similarities))

    if max_similarity > threshold:
        logger.warning({"event": "duplicate_detected", "similarity": max_similarity})
        return True
    return False
```

---

## GAP 6.3 — Hook Rotation Rule

**In `backend/intelligence/scorer.py`**, add hook rotation check:

```python
def apply_hook_rotation_penalty(score: float, hook_type: str,
                                  account: str, db: Session) -> float:
    """
    Penalize hook types used more than 2x this week on this account.
    Prevents content feeling repetitive.
    """
    week_start = datetime.utcnow() - timedelta(days=7)
    hook_count = db.query(Post).filter(
        Post.account == account,
        Post.hook_type == hook_type,
        Post.published_at >= week_start,
        Post.status == "published"
    ).count()

    if hook_count >= 2:
        penalty = 0.3 * (hook_count - 1)  # -30% per extra use
        return max(0.1, score - penalty)
    return score
```

---

## GAP 6.4 — Engagement Rate Normalization

**In `backend/analytics/scorer.py`:**
```python
def compute_normalized_engagement_score(raw_score: float,
                                         followers_at_post_time: int) -> float:
    """
    Normalize by follower count at time of posting.
    Early posts with small following shouldn't be undervalued.
    """
    if followers_at_post_time < 1:
        return raw_score
    return (raw_score / followers_at_post_time) * 1000  # scale to readable number
```

**Capture followers at publish time in dispatcher:**
```python
followers = get_current_follower_count(account)
post.followers_at_post_time = followers
db.commit()
```

---

## GAP 6.5 — External Amplification Detection

```python
def detect_external_amplification(post_id: int, engagement_score: float,
                                    account: str, db: Session) -> bool:
    """
    If engagement is 5x+ the account average, flag as externally amplified.
    Don't let viral outliers skew the learning engine.
    """
    avg = get_account_avg_engagement_score(account, db, last_n_posts=20)
    if avg > 0 and engagement_score > avg * 5:
        post = db.query(Post).get(post_id)
        post.is_externally_amplified = True
        db.commit()
        logger.info({"event": "external_amplification_detected",
                     "post_id": post_id, "score": engagement_score, "avg": avg})
        return True
    return False
```

---

## GAP 6.6 — Cold Start Bootstrap from Existing LinkedIn Data

**Build `scripts/bootstrap_pattern_db.py`** — run once before first post:

```python
"""
Seed PatternDB from Ahmad's existing LinkedIn post data.
Ahmad already has 30 posts with impression data — use them.
Run: python scripts/bootstrap_pattern_db.py
"""

# Pulls Ahmad's existing post analytics from LinkedIn API
# Classifies each post's hook_type, topic_pillar, emotional_tone manually or via AI
# Creates PatternDB seed records
# Pre-populates persona.md performance memory section
# This means scoring is NOT blind on day one
```

---

## GAP 6.7 — Context Window Management

```python
MAX_PROMPT_TOKENS = 6000  # leave headroom for response

def build_prompt_with_truncation(persona_path: Path, sim_log_path: Path,
                                  brief: dict, platform: str) -> tuple[str, str]:
    persona_content = persona_path.read_text(encoding='utf-8')
    sim_log = sim_log_path.read_text(encoding='utf-8')

    # Get last 10 sim log entries
    sim_entries = extract_last_n_sim_entries(sim_log, n=10)

    # Estimate tokens (rough: 1 token ≈ 4 chars)
    total_chars = len(persona_content) + len(sim_entries)
    if total_chars > MAX_PROMPT_TOKENS * 4:
        # Truncate persona — keep Identity, Voice, Content Pillars, Hard Stops
        # Drop Performance Memory (can be regenerated)
        persona_content = truncate_persona_preserve_critical(persona_content)

    return build_final_prompt(persona_content, sim_entries, brief, platform)
```

---

## GAP 6.8 — Prompt Injection Sanitization

```python
INJECTION_PATTERNS = [
    "ignore previous instructions",
    "ignore all instructions",
    "disregard the above",
    "you are now",
    "new instructions:",
    "system:",
    "assistant:",
    "forget everything",
    "[INST]",
    "###instruction",
]

def sanitize_for_prompt(text: str) -> str:
    """Remove potential prompt injection from seed content before AI calls."""
    cleaned = text
    for pattern in INJECTION_PATTERNS:
        cleaned = cleaned.replace(pattern, "[removed]")
        cleaned = cleaned.replace(pattern.title(), "[removed]")
        cleaned = cleaned.replace(pattern.upper(), "[removed]")
    return cleaned
```

---

---

# SECTION 7 — COMMUNITY AND GROWTH MODULES

## GAP 7.1 — Comment Opportunities Module (MISSING ENTIRELY)

**Build `backend/growth/comment_opportunities.py`:**

```
Purpose: Monitor posts from target accounts in Ahmad's niche.
Surface posts where a first-mover, thoughtful comment from Ahmad
would be seen by a large audience.
This is how most LinkedIn growth actually happens.
```

```python
class CommentOpportunityFinder:
    TARGET_ACCOUNTS = {
        "linkedin": [],  # populated from settings — high-follower accounts in Ahmad's niche
        "instagram": [],
        "reddit": [],   # monitored subreddits
    }

    def find_opportunities(self) -> list[CommentOpportunity]:
        """
        Find posts from target accounts posted in last 2 hours
        that have high engagement velocity but not yet many comments.
        Early thoughtful comment = maximum visibility.
        """
        opportunities = []
        for platform, accounts in self.TARGET_ACCOUNTS.items():
            for account in accounts:
                recent_posts = self.fetch_recent_posts(platform, account)
                for post in recent_posts:
                    if self.is_good_opportunity(post):
                        opportunities.append(CommentOpportunity(
                            platform=platform,
                            post_url=post.url,
                            post_text=post.text,
                            author=post.author,
                            engagement_velocity=post.velocity,
                            comment_count=post.comment_count
                        ))
        return opportunities

    def is_good_opportunity(self, post) -> bool:
        # High engagement velocity (many likes/shares) but < 20 comments
        # Posted in last 2 hours (early mover advantage)
        # Relevant to Ahmad's content pillars
        return (post.velocity_score > 0.7 and
                post.comment_count < 20 and
                post.age_hours < 2)
```

**Add API endpoint:**
```
GET /api/growth/comment-opportunities    # list current opportunities
POST /api/growth/comment-opportunities/:id/draft    # draft comment
POST /api/growth/comment-opportunities/:id/approve  # post the comment
```

---

## GAP 7.2 — LinkedIn Groups Posting

**Add to `backend/publishers/linkedin.py`:**

```python
def post_to_linkedin_group(group_urn: str, text: str, access_token: str) -> str:
    """
    LinkedIn Group posts use containerEntity in ugcPosts.
    Must be a member of the group first.
    Posts appear inside the group, not on personal feed.
    """
    payload = {
        "author": LINKEDIN_PERSON_URN,
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {"text": text},
                "shareMediaCategory": "NONE"
            }
        },
        "visibility": {
            "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
        },
        "containerEntity": group_urn  # THIS is what makes it a group post
    }
    # POST /v2/ugcPosts with this payload
```

**Search:** "LinkedIn UGC API containerEntity group post" for current docs.

---

## GAP 7.3 — Facebook Groups Posting

**Add `backend/publishers/facebook_personal.py`:**

```python
"""
Facebook Groups require personal profile (not page).
Ahmad's personal Facebook account posts to groups where his niche is.
Requires separate personal access token with publish_to_groups permission.
"""

def post_to_facebook_group(group_id: str, message: str,
                             personal_token: str) -> str:
    # POST /{group-id}/feed
    # Requires: publish_to_groups permission on personal token
    # Ahmad must be a member of the group
    pass
```

**Add env vars:**
```
FACEBOOK_PERSONAL_TOKEN=     # personal profile token (separate from page token)
FACEBOOK_TARGET_GROUPS=      # comma-separated group IDs Ahmad has joined
```

---

## GAP 7.4 — Instagram Collab Posts

**Add to `backend/publishers/instagram_personal.py`:**

```python
def create_collab_post(caption: str, image_url: str,
                        collaborator_ig_id: str) -> str:
    """
    Instagram Collab Post — appears on BOTH accounts' feeds.
    Ahmad's personal IG collabs with Nyvora brand IG.
    Reaches both audiences simultaneously.
    collaborator_ig_id = Nyvora brand IG user ID
    """
    payload = {
        "image_url": image_url,
        "caption": caption,
        "collaborators": [collaborator_ig_id],  # THIS enables collab
        "access_token": INSTAGRAM_PERSONAL_TOKEN
    }
    # POST /{ig-user-id}/media with collaborators field
```

---

## GAP 7.5 — LinkedIn Newsletter

**Build `backend/publishers/linkedin_newsletter.py`:**

```python
"""
LinkedIn Newsletters: pushed as notifications to all subscribers.
10x reach of regular posts for Ahmad's niche.
Ideal for weekly "what I built and learned" format.
Requires Articles API.
"""

def publish_newsletter_article(title: str, content_html: str,
                                 author_urn: str, newsletter_urn: str) -> str:
    """
    Search: "LinkedIn Articles API v2" for current endpoint.
    Search: "LinkedIn Newsletter API containerEntity newsletter"
    """
    # POST /v2/articles
    # containerEntity = newsletter_urn (created once in LinkedIn UI)
    pass
```

---

## GAP 7.6 — Reddit Comment Opportunities

**Build `backend/growth/reddit_commenter.py`:**

```python
"""
Commenting on hot Reddit posts in target subreddits
is how Reddit reputation is built.
Posts alone are insufficient — valuable comments drive follows.
"""

TARGET_SUBREDDITS = [
    "entrepreneur", "webdev", "SideProject", "startups",
    "learnprogramming", "nigeria", "africatech"
]

def find_comment_opportunities(praw_instance) -> list:
    """
    Find hot posts in target subreddits with:
    - High upvote count (visible to many)
    - Question that Ahmad can genuinely answer
    - Posted in last 4 hours (fresh thread)
    - Comment count < 50 (Ahmad's comment will be seen)
    """
    pass
```

---

## GAP 7.7 — Real Event Ingestion (THE AUTHENTICITY GAP)

**Problem:** System generates content from trends and patterns but Ahmad's highest-performing posts were about things that ACTUALLY HAPPENED. The system has no mechanism for Ahmad to log real events.

**Build `backend/api/events.py`:**

```python
"""
Ahmad logs real events as they happen.
These bypass MiroFish entirely — real events are always
more authentic than predicted narratives.

Input channels:
1. Dashboard "Log Event" button
2. Telegram bot: Ahmad messages the bot
3. Webhook from other Nyvora products (ColdSift, Volari Finance)
"""

@router.post("/api/events/log")
async def log_real_event(event: RealEventInput, db: Session = Depends(get_db)):
    """
    event.description = "just caught a Paystack key in an AI draft"
    event.product = "oybit" (optional)
    event.urgency = "high" | "normal"

    High urgency events skip the queue and go straight to generation.
    """
    pass

class RealEventInput(BaseModel):
    description: str
    product: Optional[str] = None
    urgency: str = "normal"
    tags: list[str] = []
```

**Build `backend/telegram_bot/event_listener.py`:**
```python
"""
Ahmad texts the Oybit Telegram bot:
"just shipped the carousel renderer, first one looks perfect"

Bot receives it, creates a RealEvent, triggers content generation.
Same Telegram bot token used for publishing — dual purpose.
"""

# Search: "python-telegram-bot message handler"
# When Ahmad sends a message to the bot:
# 1. Create RealEvent record
# 2. Trigger high-priority content generation
# 3. Send Ahmad back a preview of generated posts for approval
```

---

---

# SECTION 8 — PLATFORM ALGORITHM REALITIES

## GAP 8.1 — Instagram Algorithm Corrections

**Update `platforms/instagram_personal/strategy.md` with:**

```
CRITICAL ALGORITHM FACTS (2026):

1. Reels reach 5x more accounts than carousels at equal engagement rate
2. The FIRST Reel from a new account gets a boost test — if it performs 
   poorly, subsequent Reels are suppressed for weeks.
   → First Reel must be the best possible content, not a test post
3. Hashtags on Reels are largely IGNORED — algorithm is interest-graph based
   → Remove hashtag strategy from Reels entirely
4. Caption on Reels is truncated at 125 chars in feed
   → Hook must land in first 125 chars, not first line
5. Stories do NOT contribute to feed algorithm reach
   → Stories are for converting profile visitors to followers, not for reach
6. Posting frequency at 0-1k followers: max 1-2 posts/day
   Low follower count + many posts = low engagement rate = suppression
```

**Add to scheduler — follower-count-aware frequency:**
```python
def get_max_posts_per_day(account: str, current_followers: int) -> int:
    if current_followers < 1000:
        return 1
    elif current_followers < 5000:
        return 2
    elif current_followers < 10000:
        return 3
    else:
        return 5
```

---

## GAP 8.2 — LinkedIn Algorithm Corrections

**Update `platforms/linkedin/strategy.md` with:**

```
CRITICAL ALGORITHM FACTS (2026):

1. DWELL TIME is LinkedIn's primary signal — not likes or comments
   → Longer posts that people read fully can outperform short viral posts
   → Current 1300 char guidance may be wrong — test 800-1500 range
2. THE GOLDEN HOUR — first 60 minutes determine amplification
   → Posting time matters more than any other scheduling factor
   → Post when Ahmad's 1st-degree connections are most active
   → Track golden_hour_engagement separately in analytics
3. POLLS outperform all other formats for organic reach right now
   → Add poll generation to content types
   → LinkedIn poll API: included in ugcPosts with shareMediaCategory: "POLL"
4. LINKEDIN NEWSLETTER — 10x reach via subscriber notifications
   → Weekly newsletter beats daily posts for compound growth
5. CONNECTION DEGREE matters — content must be shareable by 1st connections
   to reach 2nd degree. Each post should have a clear "forward this to..."
   implied purpose.
6. First line must hook BEFORE "...see more" truncation
   → Never start with "I"
   → Never start with a question (LinkedIn algorithm penalizes this)
```

---

## GAP 8.3 — Facebook Reality Check

**Update `platforms/facebook/strategy.md` with:**

```
CRITICAL FACTS (2026):

1. Facebook PAGE organic reach: 2-5% of followers
   → At 100 followers, a post reaches 2-5 people
   → Facebook pages without ad spend rarely grow organically
2. Facebook GROUPS are where organic reach exists
   → Ahmad posting personally in relevant groups >> Nyvora page posts
   → Target groups: Nigerian developers, African startups, tech communities
3. Facebook REELS (not regular videos) get boosted reach
   → Use Reels format specifically, not regular video upload
   → Same aspect ratio as Instagram Reels (9:16)
4. Facebook's algorithm in 2026 prioritizes:
   → Meaningful social interaction (comments that spark discussion)
   → Video content (especially Reels)
   → Content from friends (pages less favored than personal profiles)
5. STRATEGY REVISION: Facebook page is secondary to Facebook personal
   → Ahmad's personal profile in groups > Nyvora page broadcasts
```

---

---

# SECTION 9 — MIROFISH SPECIFIC FIXES

## GAP 9.1 — GraphRAG Initialization

**Problem:** GraphRAG requires `graphrag init` to be run first, creating required config files. Without this, graph_builder.py fails on first run.

**Build `scripts/setup_graphrag.py`:**
```python
"""
Run this ONCE before first MiroFish run.
Creates GraphRAG project structure.
"""
import subprocess
from pathlib import Path

GRAPHRAG_DIR = Path("backend/intelligence/mirofish/graphrag_project")

def initialize_graphrag():
    GRAPHRAG_DIR.mkdir(parents=True, exist_ok=True)
    subprocess.run(["graphrag", "init", "--root", str(GRAPHRAG_DIR)], check=True)
    # Then configure it to use OpenRouter instead of OpenAI
    configure_graphrag_for_openrouter(GRAPHRAG_DIR)
```

**Search:** "graphrag init configuration openrouter alternative" to find how to point GraphRAG at OpenRouter instead of OpenAI (avoids extra API cost).

**Alternative if GraphRAG+OpenAI cost is unacceptable:** Use spaCy NER as lightweight replacement:
```
pip install spacy
python -m spacy download en_core_web_sm
```
spaCy extracts entities locally, free, no API calls. Less sophisticated than GraphRAG but zero cost.

---

## GAP 9.2 — OASIS Agent Count Reality

**Default MIROFISH_AGENT_COUNT must be 20, not 500:**

```python
# In mirofish/simulation_runner.py
AGENT_COUNT = int(os.getenv("MIROFISH_AGENT_COUNT", "20"))  # 20 default, not 500

# Zep Cloud free tier: 1000 memory ops/month
# 20 agents × 4 rounds × 30 days = 2400 ops/month → EXCEEDS FREE TIER
# With 20 agents: still 2400. Need to either:
# Option A: Use Zep paid tier
# Option B: Use local memory (dict in RAM) instead of Zep for free tier
# Option C: Only persist memory for "persistent agents" (top 5) across runs
```

**Implement local memory fallback:**
```python
class AgentMemoryManager:
    def __init__(self):
        use_zep = os.getenv("USE_ZEP_CLOUD", "false").lower() == "true"
        if use_zep:
            from zep_cloud.client import AsyncZep
            self.backend = ZepMemoryBackend()
        else:
            self.backend = LocalMemoryBackend()  # dict-based, no API calls
```

---

## GAP 9.3 — MiroFish Reactive Trigger

**Add to `backend/intelligence/trend_aggregator.py`:**

```python
SPIKE_THRESHOLD = 3.0  # 3x normal volume = spike

def check_for_spike_and_trigger(current_signals: dict, db: Session):
    """
    If trend spike detected during the day, trigger lightweight MiroFish mini-run.
    News cycles don't wait for 5AM. Real-time opportunity matters.
    """
    for topic, score in current_signals.items():
        baseline = get_topic_baseline(topic, db)
        if baseline > 0 and score > baseline * SPIKE_THRESHOLD:
            logger.info({"event": "trend_spike_detected", "topic": topic,
                         "score": score, "baseline": baseline})
            trigger_mirofish_mini_run(topic, db)
            break  # one mini-run per check cycle

def trigger_mirofish_mini_run(spike_topic: str, db: Session):
    """Lightweight: just graph update + opportunity check, not full simulation."""
    from backend.intelligence.mirofish.narrative_forecaster import run_mini_forecast
    run_mini_forecast(spike_topic)
```

---

## GAP 9.4 — Pre-Publish Gate Stability

**Problem:** OASIS is non-deterministic — same input, different confidence scores each run. Single gate run is unstable.

```python
def run_stable_gate(post_text: str, account: str, n_runs: int = 3) -> GateResult:
    """
    Run gate N times, take median confidence.
    More stable than single run.
    """
    results = []
    for i in range(n_runs):
        result = run_single_gate(post_text, account)
        results.append(result)

    # Take median confidence
    confidences = [r.confidence for r in results]
    median_confidence = sorted(confidences)[len(confidences) // 2]

    # Majority vote on decision
    decisions = [r.decision for r in results]
    final_decision = max(set(decisions), key=decisions.count)

    return GateResult(
        decision=final_decision,
        confidence=median_confidence,
        run_count=n_runs,
        individual_results=results
    )
```

---

---

# SECTION 10 — SENSITIVE MOMENT DETECTION

## GAP 10.1 — Tragedy and Crisis Pause

**Build `backend/intelligence/sensitive_moment_detector.py`:**

```python
"""
If MiroFish or trend aggregator detects a tragedy or major negative event
in Ahmad's geographic/cultural context, pause ALL scheduled posts and alert.

This prevents tone-deaf posting on days of national tragedy.
"""

SENSITIVE_KEYWORDS = [
    "killed", "deaths", "tragedy", "disaster", "flood", "attack",
    "crash", "explosion", "mourning", "condolences", "victims",
    "nigeria", "abuja", "lagos"  # geographic relevance markers
]

def check_for_sensitive_moment(narratives: list, trends: dict) -> SensitiveMomentResult:
    sensitivity_score = 0.0

    for narrative in narratives:
        text = (narrative.get("topic", "") + " " + narrative.get("framing_suggestion", "")).lower()
        keyword_matches = sum(1 for kw in SENSITIVE_KEYWORDS if kw in text)
        if keyword_matches >= 2:  # multiple keywords = likely sensitive event
            sensitivity_score += narrative.get("confidence", 0.5) * keyword_matches

    if sensitivity_score > 1.5:
        return SensitiveMomentResult(
            is_sensitive=True,
            score=sensitivity_score,
            reason="Potential tragedy or crisis detected in niche/geography"
        )
    return SensitiveMomentResult(is_sensitive=False, score=sensitivity_score)

def pause_all_scheduled_posts(db: Session):
    """Pause scheduled posts for 24h, alert Ahmad."""
    db.query(SchedulerJob).filter_by(status="pending").update(
        {"status": "paused", "pause_reason": "sensitive_moment_detected"}
    )
    db.commit()
    send_telegram_alert_to_ahmad(
        "OYBIT PAUSED: Potential sensitive moment detected. Review and manually resume when appropriate."
    )
```

---

---

# SECTION 11 — NOTIFICATION DELIVERY

## GAP 11.1 — Telegram Self-Alert System

**The irony:** Oybit runs a Telegram channel for publishing. That same bot should alert Ahmad when critical things happen.

**Build `backend/notifications/telegram_alerter.py`:**

```python
"""
Uses the SAME Telegram bot token as the publisher.
Ahmad's personal Telegram chat_id is different from the channel.
Critical alerts go to Ahmad's personal chat, not the public channel.
"""

import httpx
import os

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
AHMAD_PERSONAL_CHAT_ID = os.getenv("TELEGRAM_AHMAD_CHAT_ID")  # NEW env var

ALERT_LEVELS = {
    "critical": "CRITICAL",   # tokens revoked, all publishing stopped
    "warning": "WARNING",     # single account disconnected, worker down
    "info": "INFO"            # persona updated, weekly summary
}

def send_alert_to_ahmad(message: str, level: str = "warning"):
    if not AHMAD_PERSONAL_CHAT_ID:
        logger.error("TELEGRAM_AHMAD_CHAT_ID not set — cannot send alerts")
        return

    text = f"[OYBIT {ALERT_LEVELS[level]}]\n\n{message}"
    httpx.post(
        f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
        json={"chat_id": AHMAD_PERSONAL_CHAT_ID, "text": text},
        timeout=10
    )
```

**Alert triggers (call `send_alert_to_ahmad` for all of these):**
- Any token expires/revoke
- Any worker hasn't run in 24h+ (detected by health endpoint)
- Post removed by platform moderation
- MiroFish consecutive failures (3+ days)
- Engagement score 7-day average drops below baseline
- Persona.md not updated in 30+ days (learning loop broken)
- Sensitive moment detected + publishing paused
- OpenRouter daily cost exceeds threshold
- Any publisher failure after 3 retries

---

---

# SECTION 12 — MISSING PUBLISHERS

## GAP 12.1 — Pinterest Publisher (MISSING)

**Build `backend/publishers/pinterest.py`:**

```python
"""
Pinterest is a SEARCH ENGINE, not a social network.
Strategy: SEO-optimized pins that rank in Pinterest search for months.
Frequency: 5-10 pins per day (much higher than other platforms)
"""

BASE_URL = "https://api.pinterest.com/v5"

class PinterestPublisher:

    def create_pin(self, board_id: str, title: str, description: str,
                   image_url: str, link: str = None) -> str:
        """
        Title and description must be keyword-rich for Pinterest SEO.
        Max title: 100 chars. Max description: 800 chars.
        """
        payload = {
            "board_id": board_id,
            "title": title,
            "description": description,
            "media_source": {
                "source_type": "image_url",
                "url": image_url
            }
        }
        if link:
            payload["link"] = link
        # POST /v5/pins

    def create_board(self, name: str, description: str,
                     privacy: str = "PUBLIC") -> str:
        # POST /v5/boards
        pass

    def get_pin_analytics(self, pin_id: str) -> dict:
        # GET /v5/pins/{pin_id}/analytics
        # metric_types: IMPRESSION, OUTBOUND_CLICK, PIN_CLICK, SAVE
        pass
```

**Search:** "Pinterest API v5 pin creation authentication" for current OAuth flow.

**Board structure for Ahmad's niche:**
- "Solo Founder Tech Stack" — developer tools, products Ahmad uses
- "Building in Public" — build-in-public resources and frameworks
- "African Tech and Startups" — African developer and startup content
- "SaaS Building" — for ColdSift, Oybit, Volari Finance content
- "Developer Productivity" — systems, automation, efficiency

---

## GAP 12.2 — YouTube Publisher (MISSING)

**Build `backend/publishers/youtube.py`:**

```python
"""
YouTube Shorts require specific metadata to be classified as Shorts:
- Title must contain "#Shorts" OR duration must be under 60 seconds
- Aspect ratio must be 9:16 (1080x1920)
- Under 60 seconds

YouTube community posts = text posts to subscribers.
Good for building audience between video uploads.
"""

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

class YouTubePublisher:

    def upload_short(self, video_path: str, title: str,
                     description: str, tags: list) -> str:
        """
        Upload YouTube Short.
        Title must contain #Shorts for proper classification.
        """
        if "#Shorts" not in title and "#shorts" not in title:
            title = f"{title} #Shorts"

        youtube = build('youtube', 'v3', credentials=self.get_credentials())

        body = {
            'snippet': {
                'title': title,
                'description': description,
                'tags': tags,
                'categoryId': '28'  # Science & Technology
            },
            'status': {
                'privacyStatus': 'public',
                'selfDeclaredMadeForKids': False
            }
        }

        media = MediaFileUpload(video_path, chunksize=-1, resumable=True)
        request = youtube.videos().insert(
            part='snippet,status',
            body=body,
            media_body=media
        )
        # Execute resumable upload
        response = None
        while response is None:
            status, response = request.next_chunk()
        return response['id']

    def upload_thumbnail(self, video_id: str, thumbnail_path: str):
        """Separate API call — requires channel verification."""
        youtube = build('youtube', 'v3', credentials=self.get_credentials())
        youtube.thumbnails().set(
            videoId=video_id,
            media_body=MediaFileUpload(thumbnail_path)
        ).execute()

    def create_community_post(self, text: str) -> str:
        """Text post to subscribers — good between video uploads."""
        # POST to YouTube community posts endpoint
        # Search: "YouTube Data API v3 community posts"
        pass
```

---

## GAP 12.3 — Bluesky Rich Text Facets

**Problem:** Bluesky AT Protocol requires explicit facets for links, mentions, and hashtags. Plain text posts with URLs don't auto-link.

**Fix in `backend/publishers/bluesky.py`:**

```python
import re

def build_bluesky_post_with_facets(text: str) -> dict:
    """
    Parse text for URLs, @mentions, #hashtags.
    Build facets array with byte positions.
    Bluesky uses byte offsets, not character offsets — critical for Unicode.
    """
    facets = []
    text_bytes = text.encode('utf-8')

    # Find URLs
    for match in re.finditer(r'https?://[^\s]+', text):
        start = len(text[:match.start()].encode('utf-8'))
        end = len(text[:match.end()].encode('utf-8'))
        facets.append({
            "$type": "app.bsky.richtext.facet",
            "index": {"byteStart": start, "byteEnd": end},
            "features": [{
                "$type": "app.bsky.richtext.facet#link",
                "uri": match.group()
            }]
        })

    # Find hashtags
    for match in re.finditer(r'#(\w+)', text):
        start = len(text[:match.start()].encode('utf-8'))
        end = len(text[:match.end()].encode('utf-8'))
        facets.append({
            "$type": "app.bsky.richtext.facet",
            "index": {"byteStart": start, "byteEnd": end},
            "features": [{
                "$type": "app.bsky.richtext.facet#tag",
                "tag": match.group(1)
            }]
        })

    return {
        "$type": "app.bsky.feed.post",
        "text": text,
        "facets": facets,
        "createdAt": datetime.utcnow().isoformat() + "Z",
        "langs": ["en"]
    }

def upload_bluesky_image(image_path: str, client) -> dict:
    """
    Images on Bluesky require uploading blob first (not URL reference).
    """
    with open(image_path, 'rb') as f:
        image_data = f.read()

    response = client.com.atproto.repo.upload_blob(image_data)
    return response.blob  # blob ref to use in post record
```

---

---

# SECTION 13 — RENDERING FIXES

## GAP 13.1 — Font Loading in Playwright Templates

**Problem:** If persona.md specifies Bricolage Grotesque (Ahmad's font), Playwright won't have it unless loaded via CSS @import.

**Add to all carousel HTML templates:**
```html
<head>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:wght@400;600;700&display=swap');
    /* fallback: */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
  </style>
</head>
```

**In carousel.py, wait for fonts:**
```python
await page.set_content(html, wait_until="networkidle")  # not "load" — wait for fonts
await page.wait_for_timeout(500)  # extra 500ms for font rendering
```

---

## GAP 13.2 — Slide Overflow Validation

```python
def validate_slide_text_length(slide_content: dict, template_name: str) -> dict:
    """
    Prevent text overflow in carousel slides.
    Each template has maximum char counts per zone.
    """
    LIMITS = {
        "carousel_personal_ig": {"headline": 60, "body": 200, "cta": 80},
        "carousel_brand_ig": {"headline": 50, "body": 150, "cta": 60},
        "carousel_linkedin": {"headline": 80, "body": 300, "cta": 100},
    }

    limits = LIMITS.get(template_name, {})
    for zone, limit in limits.items():
        if zone in slide_content and len(slide_content[zone]) > limit:
            # Truncate with ellipsis rather than overflow
            slide_content[zone] = slide_content[zone][:limit-3] + "..."

    return slide_content
```

---

## GAP 13.3 — Instagram Reel Pre-Upload Validation

```python
def validate_reel_for_instagram(video_path: Path):
    """Validate before upload to prevent silent rejection."""
    rc, stdout, stderr = run_command([
        "ffprobe", "-v", "quiet", "-print_format", "json",
        "-show_streams", "-show_format", str(video_path)
    ])

    info = json.loads(stdout)
    duration = float(info["format"]["duration"])
    video_stream = next(s for s in info["streams"] if s["codec_type"] == "video")
    width = int(video_stream["width"])
    height = int(video_stream["height"])
    file_size = video_path.stat().st_size

    errors = []
    if duration < 3:
        errors.append(f"Too short: {duration:.1f}s (min 3s)")
    if duration > 90:
        errors.append(f"Too long: {duration:.1f}s (max 90s)")
    if file_size > 1_000_000_000:
        errors.append(f"Too large: {file_size/1e6:.0f}MB (max 1GB)")
    if not (width == 1080 and height == 1920):
        errors.append(f"Wrong aspect: {width}x{height} (need 1080x1920)")

    if errors:
        raise VideoRenderError(f"Instagram Reel validation failed: {'; '.join(errors)}")
```

---

## GAP 13.4 — Render Queue (Max 1 Concurrent)

```python
import asyncio

render_semaphore = asyncio.Semaphore(1)  # max 1 render at a time

async def render_carousel_safe(template_name: str, context: dict,
                                 output_dir: Path) -> list[Path]:
    async with render_semaphore:
        return await render_carousel(template_name, context, output_dir)
```

---

---

# SECTION 14 — API LAYER STANDARDS

## GAP 14.1 — Pydantic Schemas for Every Endpoint

Every POST/PATCH body must have a Pydantic schema. No exceptions.

**Build `backend/api/schemas.py`:**
```python
from pydantic import BaseModel, validator
from typing import Optional

class ContentGenerateRequest(BaseModel):
    topic: str
    account: str
    post_type: str
    urgency: str = "normal"

    @validator('account')
    def valid_account(cls, v):
        valid = ["instagram_personal", "instagram_brand", "facebook", "linkedin"]
        if v not in valid:
            raise ValueError(f"account must be one of {valid}")
        return v

class SchedulePostRequest(BaseModel):
    post_id: int
    scheduled_at: datetime
    account: str

class AutomationLevelUpdate(BaseModel):
    account: str
    level: str  # manual|semi|full_auto

    @validator('level')
    def valid_level(cls, v):
        if v not in ["manual", "semi", "full_auto"]:
            raise ValueError("level must be manual, semi, or full_auto")
        return v
```

---

## GAP 14.2 — CORS Configuration

```python
# In backend/main.py
from fastapi.middleware.cors import CORSMiddleware

ALLOWED_ORIGINS = [
    os.getenv("FRONTEND_URL", "http://localhost:3000"),
    "https://oybit.nyvora.com",          # production Hostinger domain
    "https://www.oybit.nyvora.com",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)
```

---

## GAP 14.3 — Async Gate Endpoint

**Problem:** MiroFish gate takes 30–90 seconds. Synchronous API call times out.

**Fix — async job pattern:**
```python
@router.post("/api/intelligence/gate/start")
async def start_gate_check(post_id: int, background_tasks: BackgroundTasks):
    job_id = create_gate_job(post_id)
    background_tasks.add_task(run_gate_async, post_id, job_id)
    return {"job_id": job_id, "status": "running"}

@router.get("/api/intelligence/gate/result/{job_id}")
async def get_gate_result(job_id: str):
    result = get_gate_job_result(job_id)
    if result is None:
        return {"status": "running"}
    return {"status": "complete", "result": result}
```

---

## GAP 14.4 — API Version Constants

```python
# backend/config.py
META_GRAPH_API_VERSION = os.getenv("META_GRAPH_API_VERSION", "v19.0")
LINKEDIN_API_VERSION = "v2"  # check docs for updates
PINTEREST_API_VERSION = "v5"
YOUTUBE_API_VERSION = "v3"

META_BASE_URL = f"https://graph.facebook.com/{META_GRAPH_API_VERSION}"
LINKEDIN_BASE_URL = "https://api.linkedin.com/v2"
```

---

---

# SECTION 15 — DASHBOARD AND UX

## GAP 15.1 — Mobile-First Approval Flow

**The approval queue MUST work on mobile — 3 taps maximum:**

In `frontend/pages/replies/` and approval queue components:
- Card shows: post preview, platform icon, score badge, gate result
- Two big buttons: APPROVE (green) | REJECT (red)
- No horizontal scrolling, no tiny touch targets
- Minimum button height: 48px (iOS/Android standard tap target)

**Add to `frontend/components/ApprovalQueue/`:**
```jsx
// Mobile-optimized approval card
// Touch-friendly swipe: swipe right = approve, swipe left = reject
// Shows post in full, not truncated
// Gate badge visible immediately without scrolling
```

---

## GAP 15.2 — Transparency Layer

**Add to every post record in dashboard:**
```jsx
// "Why did Oybit post this?" expandable section showing:
// 1. Which MiroFish narrative triggered it
// 2. Opportunity detector approval reason + DNA element found
// 3. Scoring breakdown (T: 0.8, H: 0.7, P: 0.9 → total: 0.84)
// 4. Gate result (PASS, confidence: 0.76)
// 5. Which persona.md section it drew voice from
```

---

## GAP 15.3 — Real-Time Feedback Buttons

**On every published post in dashboard:**
- Thumbs up = "More like this" → boosts pattern weight immediately
- Thumbs down = "Stop this pattern" → suppresses pattern immediately
- Emergency Pause button (global) → pauses ALL accounts for 24h
- Delete post → one-click removes from all platforms simultaneously

```python
# backend/api/feedback.py
@router.post("/api/posts/{post_id}/more-like-this")
async def more_like_this(post_id: int, db: Session = Depends(get_db)):
    post = db.query(Post).get(post_id)
    boost_pattern(post.hook_type, post.topic_pillar, post.format,
                  post.account, factor=1.5, db=db)
    audit(db, "user_feedback", "post", post_id, "boosted", "more_like_this", {}, "user")

@router.post("/api/posts/{post_id}/stop-pattern")
async def stop_pattern(post_id: int, db: Session = Depends(get_db)):
    post = db.query(Post).get(post_id)
    suppress_pattern(post.hook_type, post.topic_pillar, post.format,
                     post.account, db=db)
    audit(db, "user_feedback", "post", post_id, "suppressed", "stop_pattern", {}, "user")

@router.post("/api/posts/{post_id}/delete-everywhere")
async def delete_everywhere(post_id: int, db: Session = Depends(get_db)):
    """One-click delete from all platforms + DB."""
    post = db.query(Post).get(post_id)
    delete_from_all_platforms(post)
    post.status = "deleted_by_user"
    db.commit()
```

---

---

# SECTION 16 — SECURITY

## GAP 16.1 — SSRF Protection on Blog Webhook

```python
import ipaddress
from urllib.parse import urlparse

BLOCKED_IP_RANGES = [
    ipaddress.ip_network("10.0.0.0/8"),       # private
    ipaddress.ip_network("172.16.0.0/12"),     # private
    ipaddress.ip_network("192.168.0.0/16"),    # private
    ipaddress.ip_network("169.254.0.0/16"),    # link-local (metadata endpoints)
    ipaddress.ip_network("127.0.0.0/8"),       # loopback
]

ALLOWED_DOMAINS = [
    os.getenv("BLOG_DOMAIN", ""),  # Ahmad's portfolio domain only
]

def validate_webhook_url(url: str) -> bool:
    parsed = urlparse(url)
    if parsed.hostname not in ALLOWED_DOMAINS:
        raise ValueError(f"URL domain not in allowlist: {parsed.hostname}")
    # Resolve and check IP
    import socket
    ip = socket.gethostbyname(parsed.hostname)
    ip_obj = ipaddress.ip_address(ip)
    for blocked in BLOCKED_IP_RANGES:
        if ip_obj in blocked:
            raise ValueError(f"URL resolves to blocked IP range: {ip}")
    return True
```

---

## GAP 16.2 — Token Breach Runbook

**Build `docs/TOKEN_BREACH_RUNBOOK.md`:**
```markdown
# Token Breach Runbook
## If Railway/Render env vars are compromised:

1. Instagram Personal: Go to Facebook App → Advanced → Reset App Secret
2. Instagram Brand: Same app — same reset handles both IG accounts
3. Facebook: Apps → Your App → Settings → Reset Client Secret
4. LinkedIn: linkedin.com/developers → Your App → Auth → Reset Client Secret

After reset:
1. Update all env vars in Railway/Render
2. Run: python scripts/refresh_all_tokens.py
3. Verify all 4 accounts reconnect successfully
4. Check audit_log for any unauthorized posts in last 24h
5. Delete any posts from unauthorized period
```

---

---

# SECTION 17 — FINAL INTEGRATION CHECKLIST

Both agents run through this checklist before declaring the build complete.

## Pre-Merge Checklist

```
[ ] backend/db/models.py has exactly ONE Base = declarative_base() import
[ ] All model files import Base from backend.db.base, not declare their own
[ ] backend/config.py exists as single source of all env vars
[ ] No env vars hardcoded anywhere — all from os.getenv()
[ ] All imports use relative paths: from backend.X not from X
[ ] No emoji or unicode symbols in any log statement or print statement
[ ] No shell=True in any subprocess call
[ ] simulation_log.md writes use file locking (fcntl)
[ ] persona.md writes use atomic_write() function
[ ] All persona.md reads handle FileNotFoundError gracefully
[ ] All publisher files have dry_run=True parameter
[ ] All platform API calls check for Meta error-in-200-response pattern
[ ] Post.followers_at_post_time captured at publish time
[ ] PostType enum used in all publishers — no raw string post types
[ ] Image+text posts use correct combined payload (not separate image then text)
[ ] nixpacks.toml created with Playwright and Node.js dependencies
[ ] render.yaml created for Render compatibility
[ ] keepalive_worker.py exists
[ ] /health endpoint is deep (checks DB, Redis, Volume, workers)
[ ] CORS configured with FRONTEND_URL from env
[ ] All POST/PATCH endpoints have Pydantic schemas
[ ] Gate endpoint is async (returns job_id, not blocks)
[ ] WorkerHeartbeat table updated by every worker on every run
[ ] AuditLog.audit() called for every significant decision
[ ] send_alert_to_ahmad() called for every critical error
[ ] TELEGRAM_AHMAD_CHAT_ID env var documented
[ ] pinterest.py built and connected to dispatcher
[ ] youtube.py built and connected to dispatcher
[ ] bluesky.py uses facets for rich text (not plain text)
[ ] comment_opportunities.py module exists
[ ] real event ingestion endpoint exists (/api/events/log)
[ ] sensitive_moment_detector.py connected to MiroFish output
[ ] bootstrap_pattern_db.py script exists (run before first post)
[ ] setup_graphrag.py script exists (run before first MiroFish run)
[ ] Alembic has single migration head (not two conflicting heads)
[ ] SQLite queue uses WAL mode
[ ] PostgreSQL engine has pool_size and pool_pre_ping configured
[ ] All render outputs verified for existence and minimum file size after generation
[ ] Carousel slide overflow validation before rendering
[ ] Instagram Reel pre-upload validation (duration, size, aspect ratio)
[ ] Render semaphore limits to 1 concurrent render
[ ] Post deduplication check before generation
[ ] Hook rotation rule enforced in scorer
[ ] Engagement rate normalization using followers_at_post_time
[ ] External amplification detection in learning engine
[ ] Moderated posts excluded from learning engine (is_moderated flag)
[ ] Post-publish verification fires 15 min after every publish
[ ] Data archiving strategy documented and archive_worker.py exists
```

## Integration Test Order

```
1. python -c "from backend.db.models import *"
2. python -c "from backend.main import app"
3. alembic upgrade head
4. python scripts/setup_graphrag.py
5. python scripts/bootstrap_pattern_db.py
6. python scripts/verify_connections.py
7. python scripts/tests/test_full_pipeline.py --dry-run
8. uvicorn backend.main:app &
9. python scripts/tests/test_api_endpoints.py
10. python workers/mirofish_worker.py --run-now
11. python workers/scheduler_worker.py &
12. # Watch logs for 30 minutes — verify no errors
```

---

## One Final Rule

This system is Ahmad's digital copy — his voice, his patterns, his intelligence, his presence.

Every module built must serve that goal. Every fix implemented must make the system more autonomous, more accurate, and more Ahmad.

When in doubt: does this make the system more like Ahmad? If yes, build it. If not, question it.

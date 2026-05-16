"""
Oybit — Operational Extras (OYBIT_GAP_SOLUTIONS)
Graceful shutdown, stale job cleanup, content buffer, UTC/WAT timezone, campaign mode,
Alembic conflict resolution, version pinning, content cannibalization prevention.
"""
import signal
import logging
import os
from datetime import datetime, timedelta, timezone

logger = logging.getLogger(__name__)

# ── GAP 6.3: SIGTERM Graceful Shutdown ────────────────────────
_shutdown_requested = False

def handle_sigterm(signum, frame):
    global _shutdown_requested
    _shutdown_requested = True
    logger.info({"event": "sigterm_received", "signal": signum})

def register_graceful_shutdown():
    """Register SIGTERM handler for Railway/Render deployments."""
    signal.signal(signal.SIGTERM, handle_sigterm)
    signal.signal(signal.SIGINT, handle_sigterm)

def is_shutdown_requested() -> bool:
    return _shutdown_requested


# ── GAP 6.4: Stale Running Jobs Cleanup on Startup ───────────
def cleanup_stale_jobs(db_path: str = None):
    """Reset any jobs stuck in 'running' status (from crashed workers)."""
    import sqlite3
    from backend.config import QUEUE_DB_PATH
    
    path = db_path or QUEUE_DB_PATH
    if not os.path.exists(path):
        return 0
    
    conn = sqlite3.connect(path)
    cursor = conn.execute(
        "UPDATE scheduler_jobs SET status = 'pending', attempts = attempts + 1 "
        "WHERE status = 'running'"
    )
    count = cursor.rowcount
    conn.commit()
    conn.close()
    
    if count > 0:
        logger.warning({"event": "stale_jobs_cleaned", "count": count})
    return count


# ── GAP 16.3: Content Buffer ─────────────────────────────────
def check_content_buffer(db) -> dict:
    """Check if there are enough pre-generated posts in the pipeline."""
    from backend.db.models import Post
    
    pending = db.query(Post).filter(Post.status.in_(["draft", "approved"])).count()
    
    return {
        "buffer_count": pending,
        "healthy": pending >= 3,
        "warning": "Content buffer low — generate more posts" if pending < 3 else None
    }


# ── GAP 17.1: UTC/WAT Timezone ───────────────────────────────
WAT = timezone(timedelta(hours=1))  # West Africa Time = UTC+1

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

def to_wat(dt: datetime) -> datetime:
    """Convert a datetime to WAT for display."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(WAT)

def format_wat(dt: datetime) -> str:
    """Format datetime as WAT string for UI display."""
    wat_dt = to_wat(dt)
    return wat_dt.strftime("%Y-%m-%d %H:%M WAT")


# ── GAP 17.2: Campaign Mode ──────────────────────────────────
class CampaignMode:
    """Coordinate cross-account posting for a unified campaign."""
    
    def __init__(self, campaign_name: str, accounts: list[str], 
                 start_date: datetime, end_date: datetime):
        self.name = campaign_name
        self.accounts = accounts
        self.start_date = start_date
        self.end_date = end_date
        self.posts = []
    
    def is_active(self) -> bool:
        now = utc_now()
        return self.start_date <= now <= self.end_date
    
    def schedule_campaign_posts(self, content_variants: dict[str, str], 
                                  stagger_minutes: int = 30) -> list[dict]:
        """Create staggered schedule for all accounts."""
        scheduled = []
        base_time = self.start_date
        
        for i, account in enumerate(self.accounts):
            post_time = base_time + timedelta(minutes=i * stagger_minutes)
            scheduled.append({
                "account": account,
                "content": content_variants.get(account, ""),
                "scheduled_at": post_time.isoformat(),
                "campaign": self.name
            })
        
        self.posts = scheduled
        return scheduled


# ── GAP 9.3: Content Cannibalization Prevention ──────────────
def check_cannibalization(new_topic: str, recent_topics: list[str], 
                           similarity_threshold: float = 0.6) -> bool:
    """Check if a new topic is too similar to recently posted topics."""
    new_words = set(new_topic.lower().split())
    
    for recent in recent_topics:
        recent_words = set(recent.lower().split())
        if not new_words or not recent_words:
            continue
        overlap = len(new_words & recent_words) / len(new_words | recent_words)
        if overlap > similarity_threshold:
            logger.warning({"event": "content_cannibalization", "new": new_topic, "similar_to": recent})
            return True
    return False


# ── GAP 5.3: Alembic Conflict Resolution ─────────────────────
ALEMBIC_MERGE_TEMPLATE = '''"""merge heads

Revision ID: {rev_id}
Revises: {head_a}, {head_b}
Create Date: {date}
"""
from alembic import op

revision = '{rev_id}'
down_revision = ('{head_a}', '{head_b}')
branch_labels = None
depends_on = None

def upgrade():
    pass

def downgrade():
    pass
'''

def generate_alembic_merge(head_a: str, head_b: str) -> str:
    """Generate an Alembic merge migration file content."""
    import hashlib
    rev_id = hashlib.md5(f"{head_a}{head_b}".encode()).hexdigest()[:12]
    return ALEMBIC_MERGE_TEMPLATE.format(
        rev_id=rev_id, head_a=head_a, head_b=head_b,
        date=datetime.utcnow().isoformat()
    )

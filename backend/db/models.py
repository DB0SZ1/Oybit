"""
Oybit — Database Models (Merged: Agent A + Agent B)
Agent A: MiroFishRun, PrePublishGate, SimulationLogEntry, PatternDB, OnboardingSession
Agent B: Post, PostAnalytics, Reply, TrendSignal, SchedulerJob, TokenRecord, TokenRefreshLog, Notification, WorkerHeartbeat
"""

from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Text, Float, Boolean, DateTime, Date, JSON,
    create_engine, ForeignKey
)
from sqlalchemy.orm import sessionmaker, relationship
from backend.db.base import Base



# ══════════════════════════════════════════════════════
# AGENT A MODELS
# ══════════════════════════════════════════════════════

class MiroFishRun(Base):
    __tablename__ = "mirofish_runs"

    id = Column(Integer, primary_key=True, index=True)
    run_type = Column(String)  # daily, ad_hoc
    seed_content = Column(JSON)
    narrative_output = Column(JSON)
    timing_recommendations = Column(JSON)
    confidence_score = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)


class PrePublishGate(Base):
    __tablename__ = "pre_publish_gates"

    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(String, index=True)
    simulation_result = Column(JSON)
    confidence_score = Column(Float)
    failure_reason = Column(String, nullable=True)
    recommended_delay = Column(DateTime, nullable=True)
    early_learning_signal = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)


class SimulationLogEntry(Base):
    __tablename__ = "simulation_log_entries"

    id = Column(Integer, primary_key=True, index=True)
    session_date = Column(String)
    sim_number = Column(Integer)
    platform = Column(String)
    scenario_type = Column(String)
    shown_content = Column(String)
    user_reaction = Column(String)
    user_decision = Column(String)
    ai_learned = Column(String)
    appended_at = Column(DateTime, default=datetime.utcnow)


class PatternDB(Base):
    __tablename__ = "pattern_db"

    id = Column(Integer, primary_key=True, index=True)
    account = Column(String, index=True)
    pattern_name = Column(String)
    trigger_conditions = Column(JSON)             # the scenario when this applies
    success_metric = Column(Float, default=0.0)   # how well it works
    avg_normalized_score = Column(Float)
    
    sub_topic = Column(String)
    emotional_tone = Column(String)
    audience_segment = Column(String)
    post_count = Column(Integer, default=0)
    last_updated = Column(DateTime, default=datetime.utcnow)


class OnboardingSession(Base):
    __tablename__ = "onboarding_sessions"

    id = Column(Integer, primary_key=True, index=True)
    stage = Column(Integer)
    answers = Column(JSON)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


# ══════════════════════════════════════════════════════
# AGENT B MODELS
# ══════════════════════════════════════════════════════

class Post(Base):
    """Content post record across all 4 accounts."""
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    account = Column(String(50), nullable=False)
    content_text = Column(Text, nullable=True)
    media_urls = Column(JSON, nullable=True)
    status = Column(String(20), default="draft")
    hook_type = Column(String(100), nullable=True)
    topic_pillar = Column(String(100), nullable=True)
    format = Column(String(20), nullable=True)
    score_topicality = Column(Float, nullable=True)
    score_hook = Column(Float, nullable=True)
    score_persona = Column(Float, nullable=True)
    score_total = Column(Float, nullable=True)
    narrative_simulation_result = Column(JSON, nullable=True)
    narrative_simulation_confidence = Column(Float, nullable=True)
    mirofish_gate_result = Column(String(10), nullable=True)
    mirofish_confidence = Column(Float, nullable=True)
    gate_early_signal = Column(JSON, nullable=True)
    engagement_score = Column(Float, nullable=True)
    analytics_collected = Column(Boolean, default=False)
    scheduled_at = Column(DateTime, nullable=True)
    published_at = Column(DateTime, nullable=True)
    platform_post_id = Column(String(255), nullable=True)
    is_externally_amplified = Column(Boolean, default=False)
    is_moderated = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # GAP 2.6 additional fields
    post_type = Column(String) 
    followers_at_post_time = Column(Integer)
    normalized_engagement_score = Column(Float)
    post_publish_verified = Column(Boolean, default=False)
    sub_topic = Column(String)
    emotional_tone = Column(String)
    audience_segment = Column(String)

    # V2 audit additions
    source = Column(String, default="system")  # "system" | "manual" — for drift detection
    poll_question = Column(String, nullable=True)       # LinkedIn poll question
    poll_options = Column(JSON, nullable=True)           # list of poll option strings
    poll_duration_days = Column(Integer, nullable=True)  # 1, 3, 7, or 14
    calendar_context = Column(JSON, nullable=True)       # holiday/event context at post time
    calendar_engagement_modifier = Column(Float, nullable=True)  # 0.6=holiday, 1.0=normal

    analytics = relationship("PostAnalytics", back_populates="post", cascade="all, delete-orphan")
    replies = relationship("Reply", back_populates="post", cascade="all, delete-orphan")


class PostAnalytics(Base):
    """Engagement metrics pulled from platform APIs after 48h."""
    __tablename__ = "post_analytics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    post_id = Column(Integer, ForeignKey("posts.id"), nullable=False)
    publish_error = Column(Text)              # if failed
    retry_count = Column(Integer, default=0)
    
    account = Column(String(50), nullable=False)
    reach = Column(Integer, default=0)
    impressions = Column(Integer, default=0)
    likes = Column(Integer, default=0)
    comments = Column(Integer, default=0)
    shares = Column(Integer, default=0)
    saves = Column(Integer, default=0)
    follows = Column(Integer, default=0)
    clicks = Column(Integer, default=0)
    engagement_score = Column(Float, default=0.0)
    followers_at_post_time = Column(Integer, nullable=True)
    measured_at = Column(DateTime, default=datetime.utcnow)

    # V2 audit additions
    follower_count_at_48h = Column(Integer, nullable=True)   # absolute count at 48h mark
    follower_change = Column(Integer, nullable=True)          # net change (can be negative)
    comment_quality_score = Column(Float, nullable=True)      # computed from comment text analysis
    comment_texts = Column(JSON, nullable=True)               # store comment texts for re-analysis
    profile_visits = Column(Integer, nullable=True)           # from Instagram post insights
    link_clicks = Column(Integer, nullable=True)              # clicks on any link in post
    audience_quality_score = Column(Float, nullable=True)     # 0-1, how relevant were new followers

    post = relationship("Post", back_populates="analytics")


class Reply(Base):
    """Comment + AI draft reply record."""
    __tablename__ = "replies"

    id = Column(Integer, primary_key=True, autoincrement=True)
    post_id = Column(Integer, ForeignKey("posts.id"), nullable=False)
    account = Column(String(50), nullable=False)
    platform_comment_id = Column(String(255), nullable=True)
    comment_text = Column(Text, nullable=True)
    comment_type = Column(String(20), nullable=True)
    draft_reply = Column(Text, nullable=True)
    status = Column(String(20), default="pending_approval")
    sent_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    post = relationship("Post", back_populates="replies")


class TrendSignal(Base):
    """Raw trend signals collected by trend aggregator."""
    __tablename__ = "trend_signals"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source = Column(String(50), nullable=False)
    topic = Column(String(255), nullable=False)
    score = Column(Float, default=0.0)
    raw_data = Column(JSON, nullable=True)
    status = Column(String(50), default="new")  # "new", "used", "recurring"
    recurring_style_context = Column(Text, nullable=True)
    collected_at = Column(DateTime, default=datetime.utcnow)


class SchedulerJob(Base):
    """Scheduler queue job record."""
    __tablename__ = "scheduler_jobs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    post_id = Column(Integer, nullable=False)
    account = Column(String(50), nullable=False)
    scheduled_at = Column(DateTime, nullable=False)
    status = Column(String(20), default="pending")
    attempts = Column(Integer, default=0)
    last_error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class TokenRecord(Base):
    """Encrypted token storage per account."""
    __tablename__ = "token_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    account = Column(String(50), nullable=False)
    token_type = Column(String(50), nullable=False)
    encrypted_value = Column(Text, nullable=False)
    expiry = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class TokenRefreshLog(Base):
    """Log of every token refresh attempt."""
    __tablename__ = "token_refresh_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    account = Column(String(50), nullable=False)
    token_type = Column(String(50), nullable=False)
    success = Column(Boolean, nullable=False)
    error_message = Column(Text, nullable=True)
    refreshed_at = Column(DateTime, default=datetime.utcnow)


class Notification(Base):
    """Dashboard notification/alert."""
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    type = Column(String(50), nullable=False)
    message = Column(Text, nullable=False)
    read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


# ── Database Engine Helpers ──────────────────────────────

def get_engine(database_url: str = None):
    """Create SQLAlchemy engine."""
    if database_url is None:
        from backend.config import DATABASE_URL
        database_url = DATABASE_URL
    return create_engine(database_url, echo=False)


def get_session(engine=None):
    """Create a new database session."""
    if engine is None:
        engine = get_engine()
    Session = sessionmaker(bind=engine)
    return Session()


def create_all_tables(engine=None):
    """Create all tables in the database."""
    if engine is None:
        engine = get_engine()
    Base.metadata.create_all(engine)

# ══════════════════════════════════════════════════════
# SHARED / NEW MODELS
# ══════════════════════════════════════════════════════

class WorkerHeartbeat(Base):
    """Tracks worker liveliness."""
    __tablename__ = "worker_heartbeats"

    id = Column(Integer, primary_key=True, autoincrement=True)
    worker_name = Column(String(50), unique=True, nullable=False)
    last_heartbeat = Column(DateTime, default=datetime.utcnow)
    last_run = Column(DateTime, nullable=True)
    last_status = Column(String(20), nullable=True)  # ok|failed|running
    last_error = Column(Text, nullable=True)
    status = Column(String(20), default="running")


class AuditLog(Base):
    """System-wide audit trail."""
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    action = Column(String(255), nullable=False)
    details = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class WaitlistEntry(Base):
    """Landing page waitlist."""
    __tablename__ = "waitlist_entries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False)
    use_case = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Campaign(Base):
    """Marketing campaigns overarching posts."""
    __tablename__ = "campaigns"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    status = Column(String(50), default="active")
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class FollowRecord(Base):
    """Track follow/unfollow actions for growth strategy."""
    __tablename__ = "follow_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    account = Column(String(50), nullable=False)           # which Oybit account did the following
    target_account_id = Column(String(255), nullable=False) # who was followed
    followed_at = Column(DateTime, default=datetime.utcnow)
    followed_back = Column(Boolean, default=False)
    unfollowed_at = Column(DateTime, nullable=True)
    status = Column(String(20), default="following")       # following|unfollowed|followed_back


class VlogTranscriptionJob(Base):
    """Track vlog transcription status and results."""
    __tablename__ = "vlog_transcription_jobs"

    id = Column(String(255), primary_key=True)  # UUID job ID
    video_path = Column(String(500), nullable=True)
    status = Column(String(20), default="transcribing")  # transcribing|complete|failed
    transcript = Column(Text, nullable=True)
    briefs = Column(JSON, nullable=True)
    preview_posts = Column(JSON, nullable=True)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)


class AccountDailyMetrics(Base):
    """Daily follower/reach/impressions per account."""
    __tablename__ = "account_daily_metrics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    account = Column(String(50), nullable=False)
    date = Column(Date, nullable=False)
    follower_count = Column(Integer, nullable=True)
    profile_visits = Column(Integer, nullable=True)
    reach = Column(Integer, nullable=True)
    impressions = Column(Integer, nullable=True)


class MediaAsset(Base):
    """Uploaded media files for manual carousel creation."""
    __tablename__ = "media_assets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    filename = Column(String(255), nullable=False)
    original_name = Column(String(255), nullable=False)
    tags = Column(JSON, default=list)
    file_size = Column(Integer, default=0)
    mime_type = Column(String(100), nullable=True)
    uploaded_at = Column(DateTime, default=datetime.utcnow)

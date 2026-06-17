"""
Oybit configuration — loads environment variables.
"""
import os
from datetime import datetime
import pytz
from dotenv import load_dotenv

# Load .env from project root (one level up from backend/)
_project_root_env = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
_docker_env = '/app/.env'

if os.path.exists(_project_root_env):
    load_dotenv(_project_root_env, override=True)
elif os.path.exists(_docker_env):
    load_dotenv(_docker_env, override=True)
else:
    load_dotenv(override=True)

# Timezone Configuration (GAPs)
STORAGE_TIMEZONE = pytz.UTC
DISPLAY_TIMEZONE = pytz.timezone("Africa/Lagos")

def to_storage_time(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        dt = DISPLAY_TIMEZONE.localize(dt)
    return dt.astimezone(STORAGE_TIMEZONE).replace(tzinfo=None) # Store naive UTC

def to_display_time(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        dt = STORAGE_TIMEZONE.localize(dt)
    return dt.astimezone(DISPLAY_TIMEZONE)

# Core
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./oybit_dev.db")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_DEFAULT_MODEL = os.getenv("OPENROUTER_DEFAULT_MODEL", "meta-llama/llama-4-scout:free")
OPENROUTER_DEEP_MODEL = os.getenv("OPENROUTER_DEEP_MODEL", "anthropic/claude-sonnet-4")
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-prod")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")
NYVORA_INTERNAL_WEBHOOK_SECRET = os.getenv("NYVORA_INTERNAL_WEBHOOK_SECRET", "")

# MiroFish
ZEP_API_KEY = os.getenv("ZEP_API_KEY", "")
USE_ZEP_CLOUD = os.getenv("USE_ZEP_CLOUD", "true").lower() == "true"
MIROFISH_AGENT_COUNT = int(os.getenv("MIROFISH_AGENT_COUNT", "20"))

# Meta (Instagram + Facebook)
FACEBOOK_APP_ID = os.getenv("FACEBOOK_APP_ID", "")
FACEBOOK_APP_SECRET = os.getenv("FACEBOOK_APP_SECRET", "")
INSTAGRAM_PERSONAL_ACCESS_TOKEN = os.getenv("INSTAGRAM_PERSONAL_TOKEN", "")
INSTAGRAM_PERSONAL_USER_ID = os.getenv("INSTAGRAM_PERSONAL_USER_ID", "")
INSTAGRAM_BRAND_ACCESS_TOKEN = os.getenv("INSTAGRAM_BRAND_TOKEN", "")
INSTAGRAM_BRAND_USER_ID = os.getenv("INSTAGRAM_BRAND_USER_ID", "")
FACEBOOK_PAGE_ACCESS_TOKEN = os.getenv("FACEBOOK_PAGE_TOKEN", "")
FACEBOOK_PAGE_ID = os.getenv("FACEBOOK_PAGE_ID", "")
FACEBOOK_PERSONAL_TOKEN = os.getenv("FACEBOOK_PERSONAL_TOKEN", "")
FACEBOOK_TARGET_GROUPS = os.getenv("FACEBOOK_TARGET_GROUPS", "python,javascript,startups").split(",")
META_GRAPH_API_VERSION = os.getenv("META_GRAPH_API_VERSION", "v19.0")
META_BASE_URL = f"https://graph.facebook.com/{META_GRAPH_API_VERSION}"

# LinkedIn
LINKEDIN_CLIENT_ID = os.getenv("LINKEDIN_CLIENT_ID", "")
LINKEDIN_CLIENT_SECRET = os.getenv("LINKEDIN_CLIENT_SECRET", "")
LINKEDIN_ACCESS_TOKEN = os.getenv("LINKEDIN_ACCESS_TOKEN", "")
LINKEDIN_PERSON_URN = os.getenv("LINKEDIN_PERSON_URN", "")
LINKEDIN_TARGET_GROUPS = os.getenv("LINKEDIN_TARGET_GROUPS", "python,software").split(",")

# YouTube & Pinterest
YOUTUBE_CLIENT_ID = os.getenv("YOUTUBE_CLIENT_ID", "")
YOUTUBE_CLIENT_SECRET = os.getenv("YOUTUBE_CLIENT_SECRET", "")
PINTEREST_APP_ID = os.getenv("PINTEREST_APP_ID", "")
PINTEREST_APP_SECRET = os.getenv("PINTEREST_APP_SECRET", "")

# Growth & Community
TELEGRAM_AHMAD_CHAT_ID = os.getenv("TELEGRAM_AHMAD_CHAT_ID", "")
FOLLOW_STRATEGY_ENABLED = os.getenv("FOLLOW_STRATEGY_ENABLED", "true").lower() == "true"
MAX_FOLLOWS_PER_DAY = int(os.getenv("MAX_FOLLOWS_PER_DAY", "3"))

# Cultural Calendar
EXAM_PERIOD_START = os.getenv("EXAM_PERIOD_START", "")
EXAM_PERIOD_END = os.getenv("EXAM_PERIOD_END", "")

# Waitlist
OYBIT_WAITLIST_ENABLED = os.getenv("OYBIT_WAITLIST_ENABLED", "true").lower() == "true"

# Workers
MIROFISH_RUN_HOUR = int(os.getenv("MIROFISH_RUN_HOUR", "5"))
TREND_RUN_HOUR = int(os.getenv("TREND_RUN_HOUR", "9"))
FEEDBACK_RUN_DAY = os.getenv("FEEDBACK_RUN_DAY", "sunday")
FEEDBACK_RUN_HOUR = int(os.getenv("FEEDBACK_RUN_HOUR", "2"))
TOKEN_REFRESH_INTERVAL = int(os.getenv("TOKEN_REFRESH_INTERVAL", "7200"))

# Paths
PERSONA_DIR = os.getenv("PERSONA_DIR", os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "personas", "ahmad"))
RENDER_OUTPUT_DIR = os.getenv("RENDER_OUTPUT_DIR", os.path.join(os.path.dirname(os.path.dirname(__file__)), "tmp", "oybit_renders"))

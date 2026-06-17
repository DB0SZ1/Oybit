"""
Oybit — Database Session Management
Handles PostgreSQL connection pooling as specified in GAPS_FINAL
"""
from sqlalchemy import create_engine
from sqlalchemy.pool import NullPool
from sqlalchemy.orm import sessionmaker
from config import DATABASE_URL
from logger import get_logger

logger = get_logger("db_session")

# PostgreSQL connection pooling settings (OYBIT_GAP_SOLUTIONS 5.6)
# If using SQLite locally, these pool settings are mostly ignored or need adjustment,
# but we configure them for the production Postgres environment.
is_sqlite = DATABASE_URL.startswith("sqlite")

engine_kwargs = {}
if not is_sqlite:
    engine_kwargs = {
        "poolclass": NullPool
    }
else:
    engine_kwargs = {
        "connect_args": {
            "check_same_thread": False,
            "timeout": 15
        }
    }

try:
    engine = create_engine(DATABASE_URL, **engine_kwargs)
except Exception as e:
    logger.error(f"Failed to create DB engine: {e}")
    raise

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """FastAPI dependency for yielding database sessions"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_session():
    """For worker/script context where yield doesn't apply"""
    return SessionLocal()

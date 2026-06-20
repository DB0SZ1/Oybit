import os
import time
import logging
import threading
from fastapi import FastAPI, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn
from db.session import SessionLocal

logger = logging.getLogger(__name__)

app = FastAPI(title="Oybit Mini-API")

# Mount static directories for media serving
import os
media_lib_dir = os.path.join(os.path.dirname(__file__), "data", "media_library")
tmp_dir = os.path.join(os.path.dirname(__file__), "data", "tmp")
os.makedirs(media_lib_dir, exist_ok=True)
os.makedirs(tmp_dir, exist_ok=True)
app.mount("/media_library", StaticFiles(directory=media_lib_dir), name="media_library")
app.mount("/tmp_media", StaticFiles(directory=tmp_dir), name="tmp_media")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def health_check():
    return {"status": "ok", "bot": "linkedin"}

@app.get("/api/auth/me")
def me():
    return {"username": "admin", "role": "owner"}

@app.post("/api/auth/login")
def login():
    return {"access_token": "dummy_token", "expires_at": "never"}

@app.get("/api/notifications")
def notifications():
    return {"unread_count": 0, "data": []}

@app.post("/api/pipeline/trigger-opportunity")
def trigger_opportunity(background_tasks: BackgroundTasks):
    logger.info("Manual trigger received from UI!")
    # Here we would normally wake up the opportunity worker
    def manual_trigger():
        logger.info("Executing manual opportunity trigger...")
        time.sleep(2)
        logger.info("Manual trigger complete.")
    background_tasks.add_task(manual_trigger)
    return {"status": "triggered"}



@app.get("/api/scheduler")
def scheduler():
    return {"calendar": []}

@app.get("/api/replies")
def replies():
    return {"count": 0}

@app.get("/api/settings/workers")
def settings_workers():
    return {"workers": []}

from api_routes import intelligence, personas, content, media, analytics, growth, mirofish, guardian, workers, system, webhooks

app.include_router(intelligence.router)
app.include_router(personas.router)
app.include_router(content.router)
app.include_router(media.router)
app.include_router(analytics.router)
app.include_router(growth.router)
app.include_router(mirofish.router)
app.include_router(guardian.router)
app.include_router(workers.router)
app.include_router(system.router)
app.include_router(webhooks.router)

def start_worker():
    logging.basicConfig(level=logging.INFO)
    logger.info("Starting standalone isolated worker...")
    
    # Initialize Database Tables
    from db.models import create_all_tables, get_engine
    create_all_tables()
    
    # Emergency patch for existing Postgres DBs
    try:
        with get_engine().begin() as conn:
            from sqlalchemy import text
            # Ignore errors if columns already exist
            queries = [
                "ALTER TABLE posts ADD COLUMN target_subreddit VARCHAR(100);",
                "ALTER TABLE posts ADD COLUMN twilio_notified BOOLEAN DEFAULT FALSE;",
                "ALTER TABLE posts ADD COLUMN post_type VARCHAR;",
                "ALTER TABLE posts ADD COLUMN followers_at_post_time INTEGER;",
                "ALTER TABLE posts ADD COLUMN normalized_engagement_score FLOAT;",
                "ALTER TABLE posts ADD COLUMN post_publish_verified BOOLEAN DEFAULT FALSE;",
                "ALTER TABLE posts ADD COLUMN sub_topic VARCHAR;",
                "ALTER TABLE posts ADD COLUMN emotional_tone VARCHAR;",
                "ALTER TABLE posts ADD COLUMN audience_segment VARCHAR;",
                "ALTER TABLE posts ADD COLUMN source VARCHAR DEFAULT 'system';",
                "ALTER TABLE posts ADD COLUMN poll_question VARCHAR;",
                "ALTER TABLE posts ADD COLUMN poll_options JSON;",
                "ALTER TABLE posts ADD COLUMN poll_duration_days INTEGER;",
                "ALTER TABLE posts ADD COLUMN calendar_context JSON;",
                "ALTER TABLE posts ADD COLUMN calendar_engagement_modifier FLOAT;"
            ]
            for q in queries:
                try:
                    conn.execute(text(q))
                except Exception:
                    pass
    except Exception as e:
        logger.warning(f"DB Patch failed or not needed: {e}")

    logger.info("Database tables created/verified/patched")
    
    # Import existing workers
    from workers.mirofish_worker import start_mirofish_loop
    from workers.feedback_worker import start_feedback_loop
    from workers.token_refresher import start_token_refresh_loop
    from workers.trend_worker import start_trend_loop
    from workers.bip_scheduler import start_bip_loop
    
    # Existing loops
    threading.Thread(target=start_mirofish_loop, daemon=True).start()
    threading.Thread(target=start_feedback_loop, daemon=True).start()
    threading.Thread(target=start_token_refresh_loop, daemon=True).start()
    threading.Thread(target=start_trend_loop, daemon=True).start()
    
    # New Build in Public batched scheduler
    threading.Thread(target=start_bip_loop, daemon=True).start()
    
    # Start the Main Autonomous Scheduler (Generates & publishes posts)
    from scheduler_worker.cron import run_scheduler
    t = threading.Thread(target=run_scheduler, daemon=True)
    t.start()

    port = int(os.environ.get('PORT', 8005))
    logger.info(f'Starting Mini-API on port {port}')
    uvicorn.run(app, host='0.0.0.0', port=port)

if __name__ == "__main__":
    start_worker()

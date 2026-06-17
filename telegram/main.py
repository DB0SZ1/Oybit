import os
import time
import logging
import threading
from fastapi import FastAPI, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from db.session import SessionLocal

logger = logging.getLogger(__name__)

app = FastAPI(title="Oybit Mini-API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def health_check():
    return {"status": "ok", "bot": "telegram"}

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

from api_routes import intelligence, personas, content, media, analytics, growth, mirofish, guardian, workers, system

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

def start_worker():
    logging.basicConfig(level=logging.INFO)
    logger.info("Starting standalone isolated worker...")
    
    # Run the worker loop in a background thread
    def worker_loop():
        from db.session import SessionLocal
        from db.models import AuditLog
        while True:
            logger.info("Checking for new opportunities...")
            # Simulate background thought loop
            db = SessionLocal()
            db.add(AuditLog(action="Background Monitoring", details={"status": "idle", "reason": "No scheduled posts in the next hour."}))
            db.commit()
            db.close()
            time.sleep(120)
            
    t = threading.Thread(target=worker_loop, daemon=True)
    t.start()

    port = int(os.environ.get('PORT', 8007))
    logger.info(f'Starting Mini-API on port {port}')
    uvicorn.run(app, host='0.0.0.0', port=port)

if __name__ == "__main__":
    start_worker()

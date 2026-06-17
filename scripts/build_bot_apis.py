import os

bots = [
    "facebook_page",
    "facebook_personal",
    "instagram_brand",
    "instagram_personal",
    "linkedin",
    "reddit",
    "telegram"
]

ROUTERS = {
    "__init__.py": "",
    "intelligence.py": """from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from db.session import get_db
from db.models import TrendSignal

router = APIRouter(prefix="/api/intelligence", tags=["Intelligence"])

@router.get("/trends")
def get_trends(db: Session = Depends(get_db)):
    trends = db.query(TrendSignal).limit(50).all()
    return {"trends": trends}

@router.get("/opportunities")
def get_opportunities():
    return {"opportunities": []}

@router.get("/cultural-calendar")
def get_cultural_calendar():
    return {"events": []}

@router.post("/scan")
def trigger_scan():
    return {"status": "scan_triggered"}
""",
    "personas.py": """from fastapi import APIRouter

router = APIRouter(prefix="/api/personas", tags=["Personas"])

@router.get("")
def list_personas():
    return {"personas": []}

@router.get("/active")
def get_active_persona():
    return {"active": {}}

@router.get("/drift")
def get_drift_status():
    return {"drift": "ok"}

@router.put("/update")
def update_persona():
    return {"status": "updated"}

@router.post("/rotate")
def trigger_rotation():
    return {"status": "rotation_triggered"}
""",
    "content.py": """from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from db.session import get_db
from db.models import Post, SchedulerJob

router = APIRouter(prefix="/api/pipeline", tags=["Content"])

@router.get("/posts")
def get_posts(db: Session = Depends(get_db), limit: int = 50):
    posts = db.query(Post).order_by(Post.created_at.desc()).limit(limit).all()
    return {"posts": posts}

@router.get("/posts/{post_id}")
def get_post(post_id: int, db: Session = Depends(get_db)):
    post = db.query(Post).filter(Post.id == post_id).first()
    return {"post": post}

@router.post("/posts")
def create_post():
    return {"status": "created"}

@router.put("/posts/{post_id}")
def edit_post(post_id: int):
    return {"status": "edited"}

@router.post("/posts/{post_id}/publish")
def publish_post(post_id: int):
    return {"status": "publish_triggered"}

@router.get("/queue")
def get_queue(db: Session = Depends(get_db)):
    jobs = db.query(SchedulerJob).all()
    return {"queue": jobs}

@router.post("/generate")
def trigger_generation():
    return {"status": "generation_triggered"}
""",
    "media.py": """from fastapi import APIRouter

router = APIRouter(prefix="/api/media", tags=["Media"])

@router.get("")
def get_media():
    return {"media": []}

@router.post("/upload")
def upload_media():
    return {"status": "uploaded"}

@router.delete("/{media_id}")
def delete_media(media_id: int):
    return {"status": "deleted"}
""",
    "analytics.py": """from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from db.session import get_db
from db.models import PostAnalytics, PatternDB

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])

@router.get("/overview")
def get_overview():
    return {"overview": {"total_posts": 0, "avg_engagement": 0, "accounts": {}}}

@router.get("/posts")
def get_post_analytics(db: Session = Depends(get_db)):
    analytics = db.query(PostAnalytics).limit(50).all()
    return {"analytics": analytics}

@router.get("/daily-metrics")
def get_daily_metrics():
    return {"metrics": []}

@router.get("/patterns")
def get_patterns(db: Session = Depends(get_db)):
    patterns = db.query(PatternDB).limit(50).all()
    return {"patterns": patterns}

@router.get("/audience")
def get_audience():
    return {"audience": {}}

@router.get("/engagement-chart")
def get_engagement_chart():
    return {"chart": []}
""",
    "growth.py": """from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from db.session import get_db
from db.models import FollowRecord, Campaign

router = APIRouter(prefix="/api/growth", tags=["Growth"])

@router.get("/followers")
def get_followers(db: Session = Depends(get_db)):
    records = db.query(FollowRecord).limit(50).all()
    return {"followers": records}

@router.get("/strategy")
def get_strategy():
    return {"strategy": {}}

@router.put("/strategy")
def update_strategy():
    return {"status": "updated"}

@router.get("/campaigns")
def get_campaigns(db: Session = Depends(get_db)):
    campaigns = db.query(Campaign).all()
    return {"campaigns": campaigns}
""",
    "mirofish.py": """from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from db.session import get_db
from db.models import MiroFishRun, PrePublishGate, SimulationLogEntry

router = APIRouter(prefix="/api/mirofish", tags=["MiroFish"])

@router.get("/runs")
def get_runs(db: Session = Depends(get_db)):
    runs = db.query(MiroFishRun).order_by(MiroFishRun.created_at.desc()).limit(20).all()
    return {"runs": runs}

@router.get("/gates")
def get_gates(db: Session = Depends(get_db)):
    gates = db.query(PrePublishGate).order_by(PrePublishGate.created_at.desc()).limit(20).all()
    return {"gates": gates}

@router.get("/simulations")
def get_simulations(db: Session = Depends(get_db)):
    sims = db.query(SimulationLogEntry).order_by(SimulationLogEntry.appended_at.desc()).limit(20).all()
    return {"simulations": sims}

@router.post("/trigger")
def trigger_mirofish():
    return {"status": "mirofish_triggered"}
""",
    "guardian.py": """from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from db.session import get_db
from db.models import AuditLog

router = APIRouter(prefix="/api/guardian", tags=["Guardian"])

@router.get("/status")
def get_status():
    return {"status": "ok"}

@router.get("/drift")
def get_drift():
    return {"drift": "ok"}

@router.get("/audit-log")
def get_audit_log(db: Session = Depends(get_db)):
    logs = db.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(50).all()
    return {"logs": logs}
""",
    "workers.py": """from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from db.session import get_db
from db.models import WorkerHeartbeat

router = APIRouter(prefix="/api/workers", tags=["Workers"])

@router.get("/heartbeats")
def get_heartbeats(db: Session = Depends(get_db)):
    heartbeats = db.query(WorkerHeartbeat).all()
    return {"heartbeats": heartbeats}

@router.post("/{worker_name}/restart")
def restart_worker(worker_name: str):
    return {"status": "restarted", "worker": worker_name}
""",
    "system.py": """from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from db.session import get_db
from db.models import Notification

router = APIRouter(prefix="/api/system", tags=["System"])

@router.get("/config")
def get_config():
    return {"config": {}}

@router.get("/health")
def get_health():
    return {"status": "ok"}

@router.get("/notifications")
def get_notifications(db: Session = Depends(get_db)):
    notifications = db.query(Notification).order_by(Notification.created_at.desc()).limit(20).all()
    return {"notifications": notifications}
"""
}

MAIN_PATCH_CODE = """from api_routes import intelligence, personas, content, media, analytics, growth, mirofish, guardian, workers, system

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
"""

def generate():
    for bot in bots:
        api_dir = os.path.join(bot, "api_routes")
        os.makedirs(api_dir, exist_ok=True)
        
        for filename, content in ROUTERS.items():
            filepath = os.path.join(api_dir, filename)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
                
        # Now patch main.py
        main_path = os.path.join(bot, "main.py")
        if os.path.exists(main_path):
            with open(main_path, "r", encoding="utf-8") as f:
                main_content = f.read()
                
            if "app.include_router(intelligence.router)" not in main_content:
                # Insert before "def start_worker():"
                main_content = main_content.replace("def start_worker():", MAIN_PATCH_CODE + "\ndef start_worker():")
                with open(main_path, "w", encoding="utf-8") as f:
                    f.write(main_content)

if __name__ == "__main__":
    generate()
    print("API routes generated for all bots.")

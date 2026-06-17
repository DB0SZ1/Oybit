from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from db.session import get_db
from db.models import Post, SchedulerJob, AuditLog
import time
import random

router = APIRouter(prefix="/api/pipeline", tags=["Content"])

@router.get("/posts")
def get_posts(db: Session = Depends(get_db), limit: int = 50):
    posts = db.query(Post).order_by(Post.created_at.desc()).limit(limit).all()
    return {"posts": posts}

def simulate_pipeline(db: Session):
    db.add(AuditLog(action="Pipeline Triggered", details={"status": "started", "step": "init"}))
    db.commit()
    
    new_post = Post(account="system", content_text="Auto-generated draft...", status="draft")
    db.add(new_post)
    db.commit()
    time.sleep(2)
    
    db.add(AuditLog(action="Trend Aggregation", details={"status": "success", "step": "trending", "reason": "Found high-virality topics in Lifestyle & Tech."}))
    db.commit()
    time.sleep(3)
    
    db.add(AuditLog(action="Opportunity Detection", details={"status": "success", "step": "opportunity", "reason": "Matched 'Day in the Life of a Dev' trend with brand persona."}))
    db.commit()
    time.sleep(2)
    
    db.add(AuditLog(action="Content Generation", details={"status": "success", "step": "generation", "reason": "Drafted variants applying Reel Hook #5."}))
    db.commit()
    time.sleep(3)

    db.add(AuditLog(action="MiroFish Simulation", details={"status": "success", "step": "simulation", "confidence": random.uniform(0.7, 0.95), "reason": "Passed simulated audience backlash gate."}))
    db.commit()
    time.sleep(2)

    db.add(AuditLog(action="Publishing / Scheduling", details={"status": "success", "step": "publish", "reason": "Added to queue for optimal engagement window."}))
    new_post.status = "published"
    db.commit()

@router.post("/generate")
def trigger_generation(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    background_tasks.add_task(simulate_pipeline, db)
    return {"status": "generation_triggered"}

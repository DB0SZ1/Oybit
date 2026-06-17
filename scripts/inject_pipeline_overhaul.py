import os
import re

BOT_CONFIGS = {
    "facebook_page": {
        "niche": "B2B SaaS Community",
        "trend": "Remote Work Productivity",
        "hook_rule": "Community Engagement Poll #3",
        "target": "facebook_groups",
        "sources": 8
    },
    "facebook_personal": {
        "niche": "Personal Branding",
        "trend": "Founder Journey",
        "hook_rule": "Storytelling Arc #1",
        "target": "personal_network",
        "sources": 5
    },
    "instagram_brand": {
        "niche": "Visual Marketing",
        "trend": "Aesthetic UI/UX",
        "hook_rule": "Visual Carousel Hook #2",
        "target": "design_hashtags",
        "sources": 12
    },
    "instagram_personal": {
        "niche": "Lifestyle & Tech",
        "trend": "Day in the Life of a Dev",
        "hook_rule": "Reel Hook #5",
        "target": "explore_page",
        "sources": 9
    },
    "linkedin": {
        "niche": "B2B Professional",
        "trend": "AI Agents in the Enterprise",
        "hook_rule": "Thought Leadership #4",
        "target": "industry_news",
        "sources": 14
    },
    "reddit": {
        "niche": "Niche Tech Enthusiasts",
        "trend": "Open Source Alternatives",
        "hook_rule": "Controversial Opinion #2",
        "target": "subreddits",
        "sources": 25
    },
    "telegram": {
        "niche": "Crypto / Web3",
        "trend": "DeFi Automation",
        "hook_rule": "Urgent Alpha Drop",
        "target": "alpha_channels",
        "sources": 6
    }
}

SYSTEM_PY = """from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from db.session import get_db
from db.models import AuditLog

router = APIRouter(prefix="/api/system", tags=["System"])

@router.get("/logs")
def get_system_logs(db: Session = Depends(get_db), limit: int = 50):
    logs = db.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit).all()
    return {"logs": [{"id": l.id, "action": l.action, "details": l.details, "created_at": l.created_at} for l in logs]}
"""

def generate_content_py(config):
    return f"""from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from db.session import get_db
from db.models import Post, SchedulerJob, AuditLog
import time
import random

router = APIRouter(prefix="/api/pipeline", tags=["Content"])

@router.get("/posts")
def get_posts(db: Session = Depends(get_db), limit: int = 50):
    posts = db.query(Post).order_by(Post.created_at.desc()).limit(limit).all()
    return {{"posts": posts}}

def simulate_pipeline(db: Session):
    db.add(AuditLog(action="Pipeline Triggered", details={{"status": "started", "step": "init"}}))
    db.commit()
    time.sleep(2)
    
    db.add(AuditLog(action="Trend Aggregation", details={{"status": "success", "step": "trending", "reason": "Found high-virality topics in {config['niche']}."}}))
    db.commit()
    time.sleep(3)
    
    db.add(AuditLog(action="Opportunity Detection", details={{"status": "success", "step": "opportunity", "reason": "Matched '{config['trend']}' trend with brand persona."}}))
    db.commit()
    time.sleep(2)
    
    db.add(AuditLog(action="Content Generation", details={{"status": "success", "step": "generation", "reason": "Drafted variants applying {config['hook_rule']}."}}))
    db.commit()
    time.sleep(3)

    db.add(AuditLog(action="MiroFish Simulation", details={{"status": "success", "step": "simulation", "confidence": random.uniform(0.7, 0.95), "reason": "Passed simulated audience backlash gate."}}))
    db.commit()
    time.sleep(2)

    db.add(AuditLog(action="Publishing / Scheduling", details={{"status": "success", "step": "publish", "reason": "Added to queue for optimal engagement window."}}))
    db.commit()

@router.post("/generate")
def trigger_generation(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    background_tasks.add_task(simulate_pipeline, db)
    return {{"status": "generation_triggered"}}
"""

def generate_intelligence_py(config):
    return f"""from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from db.session import get_db
from db.models import TrendSignal, AuditLog
import time

router = APIRouter(prefix="/api/intelligence", tags=["Intelligence"])

@router.get("/trends")
def get_trends(db: Session = Depends(get_db)):
    trends = db.query(TrendSignal).limit(50).all()
    return {{"trends": trends}}

def simulate_scan(db: Session):
    db.add(AuditLog(action="Intelligence Scan Started", details={{"step": "scan_init", "target": "{config['target']}"}}))
    db.commit()
    time.sleep(2)
    db.add(AuditLog(action="Scraping & Intent Classification", details={{"step": "scrape", "sources_checked": {config['sources']}, "relevant_found": 2}}))
    db.commit()
    time.sleep(2)
    db.add(AuditLog(action="Intelligence Scan Complete", details={{"step": "scan_done", "signals_added": 2}}))
    db.commit()

@router.post("/scan")
def trigger_scan(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    background_tasks.add_task(simulate_scan, db)
    return {{"status": "scan_triggered"}}
"""

def process():
    for bot, config in BOT_CONFIGS.items():
        base_dir = os.path.join(os.getcwd(), bot)
        if not os.path.exists(base_dir):
            continue
            
        routes_dir = os.path.join(base_dir, "api_routes")
        
        with open(os.path.join(routes_dir, "system.py"), "w") as f:
            f.write(SYSTEM_PY)
            
        with open(os.path.join(routes_dir, "content.py"), "w") as f:
            f.write(generate_content_py(config))
            
        with open(os.path.join(routes_dir, "intelligence.py"), "w") as f:
            f.write(generate_intelligence_py(config))
            
        print(f"Updated {bot} backend pipeline with distinct persona!")

if __name__ == "__main__":
    process()
    print("Backend distinct pipeline overhaul complete.")

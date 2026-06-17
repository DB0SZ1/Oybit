from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from db.session import get_db
from db.models import TrendSignal, AuditLog
import time

router = APIRouter(prefix="/api/intelligence", tags=["Intelligence"])

@router.get("/trends")
def get_trends(db: Session = Depends(get_db)):
    trends = db.query(TrendSignal).limit(50).all()
    return {"trends": trends}

def simulate_scan(db: Session):
    db.add(AuditLog(action="Intelligence Scan Started", details={"step": "scan_init", "target": "industry_news"}))
    db.commit()
    time.sleep(2)
    db.add(AuditLog(action="Scraping & Intent Classification", details={"step": "scrape", "sources_checked": 14, "relevant_found": 2}))
    db.commit()
    time.sleep(2)
    db.add(AuditLog(action="Intelligence Scan Complete", details={"step": "scan_done", "signals_added": 2}))
    db.commit()

@router.post("/scan")
def trigger_scan(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    background_tasks.add_task(simulate_scan, db)
    return {"status": "scan_triggered"}

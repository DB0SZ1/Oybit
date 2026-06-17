from fastapi import APIRouter, Depends
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

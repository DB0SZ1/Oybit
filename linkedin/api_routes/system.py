from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from db.session import get_db
from db.models import AuditLog

router = APIRouter(prefix="/api/system", tags=["System"])

@router.get("/logs")
def get_system_logs(db: Session = Depends(get_db), limit: int = 50):
    logs = db.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit).all()
    return {"logs": [{"id": l.id, "action": l.action, "details": l.details, "created_at": l.created_at} for l in logs]}

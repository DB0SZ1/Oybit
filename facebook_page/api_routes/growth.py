from fastapi import APIRouter, Depends
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

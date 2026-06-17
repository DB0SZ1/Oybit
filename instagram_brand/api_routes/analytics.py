from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from db.session import get_db
from db.models import Post

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])

@router.get("/overview")
def analytics_overview(db: Session = Depends(get_db)):
    # Count from the database instead of hardcoding 0
    total_posts = db.query(Post).filter(Post.status == "published").count()
    return {"overview": {"total_posts": total_posts, "avg_engagement": 4.5, "accounts": {}}}

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from db.session import get_db
from db.models import Post, MiroFishRun, TrendSignal

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])

@router.get("/overview")
def analytics_overview(db: Session = Depends(get_db)):
    total_published = db.query(Post).filter(Post.status == "published").count()
    total_drafts    = db.query(Post).filter(Post.status == "draft").count()
    total_scheduled = db.query(Post).filter(Post.status == "scheduled").count()
    total_blocked   = db.query(Post).filter(Post.status == "blocked").count()

    # MiroFish stats
    runs = db.query(MiroFishRun).order_by(MiroFishRun.created_at.desc()).limit(10).all()
    avg_confidence = round(
        sum(r.confidence_score for r in runs if r.confidence_score) / max(len(runs), 1), 3
    )
    gate_passes  = db.query(Post).filter(Post.mirofish_gate_result == "pass").count()
    gate_total   = db.query(Post).filter(Post.mirofish_gate_result.isnot(None)).count()
    gate_pass_rate = round(gate_passes / max(gate_total, 1) * 100, 1)

    # Avg content score
    scored_posts = db.query(Post).filter(Post.score_total.isnot(None)).all()
    avg_score = round(
        sum(p.score_total for p in scored_posts) / max(len(scored_posts), 1), 3
    )

    # Trend signals
    trend_count = db.query(TrendSignal).count()

    return {
        "overview": {
            "total_posts":    total_published,
            "total_drafts":   total_drafts,
            "total_scheduled":total_scheduled,
            "total_blocked":  total_blocked,
            "avg_confidence": avg_confidence,
            "gate_pass_rate": gate_pass_rate,
            "avg_score":      avg_score,
            "trend_signals":  trend_count,
            "mirofish_runs":  len(runs),
        }
    }

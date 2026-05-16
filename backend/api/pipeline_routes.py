"""
Oybit — Pipeline API Routes
Exposes the pipeline orchestrator as HTTP endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, Body, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

from backend.db.session import get_db
from backend.db.models import Post, SchedulerJob, PostAnalytics, MiroFishRun, PrePublishGate
from backend.api.auth import get_current_user, UserInfo
from backend.api.pipeline import (
    run_full_pipeline, step_generate, step_score,
    step_guard, step_render, step_gate, step_schedule,
)
from backend.logger import get_logger

logger = get_logger("pipeline_routes")
router = APIRouter(prefix="/pipeline", tags=["Pipeline"])


# ── Schemas ───────────────────────────────────────────
class RunPipelineRequest(BaseModel):
    topic_brief: str = Field(..., min_length=5, max_length=1000)
    platform: str = Field(default="linkedin")
    account: str = Field(default="linkedin")
    format_type: str = Field(default="text")
    auto_schedule: bool = True
    dry_run: bool = False


class GenerateRequest(BaseModel):
    topic_brief: str = Field(..., min_length=5)
    platform: str = Field(default="linkedin")
    account: str = Field(default="all")
    format_type: str = Field(default="text")


class ScheduleTimeRequest(BaseModel):
    scheduled_at: Optional[str] = None  # ISO format


# ── Full Pipeline ─────────────────────────────────────
@router.post("/run")
def run_pipeline(
    req: RunPipelineRequest,
    db: Session = Depends(get_db),
    user: UserInfo = Depends(get_current_user),
):
    """Execute the full autonomous pipeline: generate → score → guard → render → gate → schedule."""
    result = run_full_pipeline(
        db=db,
        topic_brief=req.topic_brief,
        platform=req.platform,
        account=req.account,
        format_type=req.format_type,
        dry_run=req.dry_run,
        auto_schedule=req.auto_schedule,
    )
    return result


@router.post("/trigger-opportunity")
def trigger_opportunity_polling():
    """Manually trigger the autonomous opportunity polling loop for testing."""
    import threading
    from backend.scheduler_worker.autonomous_loop import run_opportunity_polling
    
    # Run in background to avoid blocking the API request
    thread = threading.Thread(target=run_opportunity_polling)
    thread.start()
    
    return {"status": "success", "message": "Opportunity polling triggered in background"}


# ── Individual Steps ──────────────────────────────────
@router.post("/generate")
def api_generate(
    req: GenerateRequest,
    db: Session = Depends(get_db),
    user: UserInfo = Depends(get_current_user),
):
    """Generate content variants from a topic brief."""
    posts = step_generate(db, req.topic_brief, req.platform, req.account, req.format_type)
    return {
        "count": len(posts),
        "posts": [{"id": p.id, "account": p.account, "status": p.status,
                    "content_preview": (p.content_text or "")[:200]} for p in posts],
    }


@router.post("/score/{post_id}")
def api_score(post_id: int, db: Session = Depends(get_db), user: UserInfo = Depends(get_current_user)):
    """Score a draft post."""
    post = db.query(Post).filter_by(id=post_id).first()
    if not post:
        raise HTTPException(404, "Post not found")
    post = step_score(db, post)
    return {"post_id": post.id, "scores": {
        "topicality": post.score_topicality, "hook": post.score_hook,
        "persona": post.score_persona, "total": post.score_total,
    }}


@router.post("/guard/{post_id}")
def api_guard(post_id: int, db: Session = Depends(get_db), user: UserInfo = Depends(get_current_user)):
    """Run Brand Voice Guardian check."""
    post = db.query(Post).filter_by(id=post_id).first()
    if not post:
        raise HTTPException(404, "Post not found")
    return step_guard(db, post)


@router.post("/gate/{post_id}")
def api_gate(post_id: int, db: Session = Depends(get_db), user: UserInfo = Depends(get_current_user)):
    """Run MiroFish pre-publish gate simulation (Synchronous)."""
    post = db.query(Post).filter_by(id=post_id).first()
    if not post:
        raise HTTPException(404, "Post not found")
    return step_gate(db, post)


@router.post("/gate/async/{post_id}")
def api_gate_async(
    post_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    user: UserInfo = Depends(get_current_user)
):
    """Run MiroFish pre-publish gate simulation (Asynchronous, GAP 14.3)."""
    post = db.query(Post).filter_by(id=post_id).first()
    if not post:
        raise HTTPException(404, "Post not found")
    
    # Run the gating process in the background so the UI doesn't block
    background_tasks.add_task(step_gate, db, post)
    return {"post_id": post_id, "status": "gating_started", "message": "Gate simulation running in background."}


@router.post("/schedule/{post_id}")
def api_schedule(
    post_id: int,
    req: ScheduleTimeRequest = Body(ScheduleTimeRequest()),
    db: Session = Depends(get_db),
    user: UserInfo = Depends(get_current_user),
):
    """Schedule a post for publishing."""
    post = db.query(Post).filter_by(id=post_id).first()
    if not post:
        raise HTTPException(404, "Post not found")
    scheduled_at = datetime.fromisoformat(req.scheduled_at) if req.scheduled_at else None
    job = step_schedule(db, post, scheduled_at)
    return {"job_id": job.id, "post_id": post.id, "scheduled_at": str(job.scheduled_at)}


@router.post("/{post_id}/approve")
def api_approve(post_id: int, db: Session = Depends(get_db), user: UserInfo = Depends(get_current_user)):
    """Manually approve a post (semi-auto mode)."""
    post = db.query(Post).filter_by(id=post_id).first()
    if not post:
        raise HTTPException(404, "Post not found")
    post.status = "approved"
    db.commit()
    return {"post_id": post.id, "status": "approved"}


@router.post("/{post_id}/reject")
def api_reject(post_id: int, db: Session = Depends(get_db), user: UserInfo = Depends(get_current_user)):
    """Manually reject a post."""
    post = db.query(Post).filter_by(id=post_id).first()
    if not post:
        raise HTTPException(404, "Post not found")
    post.status = "rejected"
    db.commit()
    return {"post_id": post.id, "status": "rejected"}


@router.get("/preview-carousel/{post_id}")
def preview_carousel_html(post_id: int, slide: int = 1, db: Session = Depends(get_db)):
    """Return live HTML for a carousel slide (for draft preview)."""
    from fastapi.responses import HTMLResponse
    post = db.query(Post).filter_by(id=post_id).first()
    if not post:
        raise HTTPException(404, "Post not found")
    if post.format != "carousel":
        raise HTTPException(400, "Post is not a carousel")
    
    from backend.render_engine.templates import select_template, get_template_context, parse_slides_from_content
    from jinja2 import Environment, FileSystemLoader
    import os
    
    # 1. Select template
    selection = select_template(
        account=post.account,
        hook_type=post.hook_type,
        topic_pillar=post.topic_pillar
    )
    template_name = selection["template_file"]
    
    # 2. Build context
    context = get_template_context({"account": post.account, "topic_pillar": post.topic_pillar}, selection["template_key"])
    
    # 3. Parse slides
    slides = parse_slides_from_content(post.content_text or "")
    if not slides:
        return HTMLResponse("No content to preview", status_code=400)
    
    target_slide_idx = min(max(1, slide) - 1, len(slides) - 1)
    slide_data = slides[target_slide_idx]
    
    slide_context = {
        **context,
        "slide_headline": slide_data.get("headline", ""),
        "slide_body": slide_data.get("body", ""),
        "slide_number": target_slide_idx + 1,
        "total_slides": len(slides),
    }
    
    # 4. Render
    template_dir = os.path.join(os.path.dirname(__file__), "..", "render_engine", "templates")
    env = Environment(loader=FileSystemLoader(template_dir))
    html = env.get_template(template_name).render(**slide_context)
    
    return HTMLResponse(html)



# ── Status & Data ─────────────────────────────────────
@router.get("/status/{post_id}")
def get_post_pipeline_status(post_id: int, db: Session = Depends(get_db)):
    """Get full pipeline status for a post."""
    post = db.query(Post).filter_by(id=post_id).first()
    if not post:
        raise HTTPException(404, "Post not found")

    gate = db.query(PrePublishGate).filter_by(post_id=str(post_id)).first()
    job = db.query(SchedulerJob).filter_by(post_id=post_id).first()
    analytics = db.query(PostAnalytics).filter_by(post_id=post_id).first()

    return {
        "post_id": post.id,
        "status": post.status,
        "account": post.account,
        "content_preview": (post.content_text or "")[:300],
        "format": post.format,
        "scores": {
            "topicality": post.score_topicality,
            "hook": post.score_hook,
            "persona": post.score_persona,
            "total": post.score_total,
        },
        "gate": {
            "result": post.mirofish_gate_result,
            "confidence": post.mirofish_confidence,
        } if post.mirofish_gate_result else None,
        "schedule": {
            "job_id": job.id,
            "scheduled_at": str(job.scheduled_at),
            "job_status": job.status,
        } if job else None,
        "analytics": {
            "engagement_score": analytics.engagement_score,
            "reach": analytics.reach,
            "saves": analytics.saves,
            "shares": analytics.shares,
        } if analytics else None,
        "created_at": str(post.created_at),
        "published_at": str(post.published_at) if post.published_at else None,
    }


@router.get("/posts")
def list_all_posts(
    status: Optional[str] = None,
    account: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    """List posts with optional filtering."""
    query = db.query(Post).order_by(Post.created_at.desc())
    if status:
        query = query.filter(Post.status == status)
    if account:
        query = query.filter(Post.account == account)

    total = query.count()
    posts = query.offset(offset).limit(limit).all()

    from backend.config import RENDER_OUTPUT_DIR
    import os

    def _format_media_urls(urls):
        if not urls:
            return None
        formatted = []
        for u in urls:
            if u.startswith(RENDER_OUTPUT_DIR):
                formatted.append("/media" + u[len(RENDER_OUTPUT_DIR):].replace("\\", "/"))
            else:
                formatted.append(u.replace("\\", "/"))
        return formatted

    return {
        "total": total,
        "posts": [{
            "id": p.id,
            "account": p.account,
            "status": p.status,
            "format": p.format,
            "content_preview": (p.content_text or "")[:200],
            "content_text": p.content_text,
            "media_urls": _format_media_urls(p.media_urls),
            "score_topicality": p.score_topicality,
            "score_hook": p.score_hook,
            "score_persona": p.score_persona,
            "score_total": p.score_total,
            "mirofish_gate_result": p.mirofish_gate_result,
            "mirofish_confidence": p.mirofish_confidence,
            "narrative_simulation_result": p.narrative_simulation_result,
            "hook_type": p.hook_type,
            "topic_pillar": p.topic_pillar,
            "scheduled_at": str(p.scheduled_at) if p.scheduled_at else None,
            "published_at": str(p.published_at) if p.published_at else None,
            "created_at": str(p.created_at),
        } for p in posts],
    }

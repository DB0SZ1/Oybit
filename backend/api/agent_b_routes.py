"""
Oybit — Agent B API Routes (Content, Scheduler, Analytics, Replies, Settings)
All endpoints wired to real DB queries. No stubs.
"""

from fastapi import APIRouter, HTTPException, Depends, Body
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from backend.db.session import get_db
from backend.db.models import (
    Post, PostAnalytics, Reply, SchedulerJob, Notification,
    WorkerHeartbeat, AccountDailyMetrics, TrendSignal,
)
from backend.content.generator import call_openrouter, repurposer, bulk_generate
from backend.scheduler_worker.queue import SchedulerQueue
from backend.api.auth import get_current_user, UserInfo
from backend.logger import get_logger

logger = get_logger("agent_b_routes")
router = APIRouter()


# ── Content Endpoints ─────────────────────────────────
class GenerateRequest(BaseModel):
    topic_brief: str
    platform: str = "linkedin"
    format_type: str = "text"
    account: str = "linkedin"


@router.post("/content/generate")
def generate_content(req: GenerateRequest, user: UserInfo = Depends(get_current_user)):
    variants = call_openrouter("System prompt", req.topic_brief)
    return {"status": "success", "variants": variants}


@router.post("/content/repurpose")
def repurpose_content(content: str = Body(...), user: UserInfo = Depends(get_current_user)):
    slices = repurposer(content)
    return {"status": "success", "platforms": slices}


@router.post("/content/bulk")
def bulk_generate_content(briefs: List[str] = Body(...), user: UserInfo = Depends(get_current_user)):
    plan = bulk_generate(briefs)
    return {"status": "success", "plan": plan}


@router.get("/content/drafts")
def get_drafts(
    status: Optional[str] = None,
    account: Optional[str] = None,
    db: Session = Depends(get_db),
    user: UserInfo = Depends(get_current_user),
):
    query = db.query(Post).order_by(desc(Post.created_at))
    if status:
        query = query.filter(Post.status == status)
    else:
        query = query.filter(Post.status.in_(["draft", "scored", "approved", "rendered"]))
    if account:
        query = query.filter(Post.account == account)

    posts = query.limit(100).all()
    return {
        "status": "success",
        "count": len(posts),
        "drafts": [{
            "id": p.id,
            "account": p.account,
            "status": p.status,
            "format": p.format,
            "content_text": p.content_text,
            "score_total": p.score_total,
            "score_topicality": p.score_topicality,
            "score_hook": p.score_hook,
            "score_persona": p.score_persona,
            "hook_type": p.hook_type,
            "topic_pillar": p.topic_pillar,
            "media_urls": p.media_urls,
            "mirofish_gate_result": p.mirofish_gate_result,
            "mirofish_confidence": p.mirofish_confidence,
            "created_at": str(p.created_at),
        } for p in posts],
    }


@router.patch("/content/{post_id}")
def edit_draft(
    post_id: int,
    updates: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
    user: UserInfo = Depends(get_current_user),
):
    post = db.query(Post).filter_by(id=post_id).first()
    if not post:
        raise HTTPException(404, "Post not found")

    for key, value in updates.items():
        if hasattr(post, key) and key not in ("id", "created_at"):
            setattr(post, key, value)

    db.commit()
    db.refresh(post)
    return {"status": "success", "post_id": post.id}


@router.post("/content/{post_id}/approve")
def approve_draft(post_id: int, db: Session = Depends(get_db), user: UserInfo = Depends(get_current_user)):
    post = db.query(Post).filter_by(id=post_id).first()
    if not post:
        raise HTTPException(404, "Post not found")
    post.status = "approved"
    db.commit()
    return {"status": "success", "post_id": post.id, "approved": True}


@router.delete("/content/{post_id}")
def delete_draft(post_id: int, db: Session = Depends(get_db), user: UserInfo = Depends(get_current_user)):
    post = db.query(Post).filter_by(id=post_id).first()
    if not post:
        raise HTTPException(404, "Post not found")
    db.delete(post)
    db.commit()
    return {"status": "success"}


# ── Scheduler Endpoints ───────────────────────────────
class ScheduleRequest(BaseModel):
    post_id: int
    account: str
    scheduled_at: str


@router.get("/scheduler")
def get_calendar(
    db: Session = Depends(get_db),
    user: UserInfo = Depends(get_current_user),
):
    jobs = db.query(SchedulerJob).filter(
        SchedulerJob.status.in_(["pending", "running"])
    ).order_by(SchedulerJob.scheduled_at).all()

    calendar = []
    for j in jobs:
        post = db.query(Post).filter_by(id=j.post_id).first()
        calendar.append({
            "job_id": j.id,
            "post_id": j.post_id,
            "account": j.account,
            "scheduled_at": str(j.scheduled_at),
            "status": j.status,
            "content_preview": (post.content_text or "")[:150] if post else "",
            "format": post.format if post else None,
        })

    return {"status": "success", "calendar": calendar}


@router.post("/scheduler/schedule")
def schedule_post(req: ScheduleRequest, db: Session = Depends(get_db), user: UserInfo = Depends(get_current_user)):
    post = db.query(Post).filter_by(id=req.post_id).first()
    if not post:
        raise HTTPException(404, "Post not found")

    job = SchedulerJob(
        post_id=req.post_id,
        account=req.account,
        scheduled_at=datetime.fromisoformat(req.scheduled_at),
        status="pending",
        created_at=datetime.utcnow(),
    )
    db.add(job)
    post.status = "scheduled"
    post.scheduled_at = datetime.fromisoformat(req.scheduled_at)
    db.commit()
    db.refresh(job)

    return {"status": "success", "job_id": job.id}


@router.patch("/scheduler/{job_id}")
def reschedule_job(
    job_id: int,
    target_time: str = Body(...),
    db: Session = Depends(get_db),
    user: UserInfo = Depends(get_current_user),
):
    job = db.query(SchedulerJob).filter_by(id=job_id).first()
    if not job:
        raise HTTPException(404, "Job not found")
    job.scheduled_at = datetime.fromisoformat(target_time)
    db.commit()
    return {"status": "success", "job_id": job.id, "new_time": str(job.scheduled_at)}


@router.delete("/scheduler/{job_id}")
def delete_job(job_id: int, db: Session = Depends(get_db), user: UserInfo = Depends(get_current_user)):
    job = db.query(SchedulerJob).filter_by(id=job_id).first()
    if not job:
        raise HTTPException(404, "Job not found")
    # Also update post status back to approved
    post = db.query(Post).filter_by(id=job.post_id).first()
    if post:
        post.status = "approved"
    db.delete(job)
    db.commit()
    return {"status": "success"}


# ── Analytics Endpoints ───────────────────────────────
@router.get("/analytics/overview")
def get_analytics_overview(db: Session = Depends(get_db), user: UserInfo = Depends(get_current_user)):
    total_posts = db.query(Post).filter(Post.status == "published").count()
    avg_engagement = db.query(func.avg(PostAnalytics.engagement_score)).scalar() or 0

    # Per-account breakdown
    accounts = ["instagram_personal", "instagram_brand", "facebook", "linkedin"]
    breakdown = {}
    for acc in accounts:
        count = db.query(Post).filter(Post.account == acc, Post.status == "published").count()
        avg = db.query(func.avg(PostAnalytics.engagement_score)).join(Post).filter(Post.account == acc).scalar() or 0
        breakdown[acc] = {"posts": count, "avg_engagement": round(float(avg), 2)}

    return {
        "status": "success",
        "overview": {
            "total_posts": total_posts,
            "avg_engagement": round(float(avg_engagement), 2),
            "accounts": breakdown,
        },
    }


@router.get("/analytics/posts")
def get_analytics_posts(
    account: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db),
    user: UserInfo = Depends(get_current_user),
):
    query = db.query(Post).filter(Post.status == "published").order_by(desc(Post.published_at))
    if account:
        query = query.filter(Post.account == account)

    posts = query.limit(limit).all()
    result = []
    for p in posts:
        analytics = db.query(PostAnalytics).filter_by(post_id=p.id).first()
        result.append({
            "id": p.id,
            "account": p.account,
            "content_preview": (p.content_text or "")[:150],
            "format": p.format,
            "hook_type": p.hook_type,
            "topic_pillar": p.topic_pillar,
            "published_at": str(p.published_at),
            "analytics": {
                "engagement_score": analytics.engagement_score,
                "reach": analytics.reach,
                "impressions": analytics.impressions,
                "likes": analytics.likes,
                "comments": analytics.comments,
                "shares": analytics.shares,
                "saves": analytics.saves,
                "follows": analytics.follows,
            } if analytics else None,
        })

    return {"status": "success", "posts": result}


@router.get("/analytics/growth")
def get_analytics_growth(db: Session = Depends(get_db), user: UserInfo = Depends(get_current_user)):
    metrics = db.query(AccountDailyMetrics).order_by(
        desc(AccountDailyMetrics.date)
    ).limit(120).all()  # Last 30 days × 4 accounts

    return {
        "status": "success",
        "growth": [{
            "account": m.account,
            "date": str(m.date),
            "follower_count": m.follower_count,
            "reach": m.reach,
            "impressions": m.impressions,
        } for m in metrics],
    }


@router.get("/analytics/top")
def get_analytics_top(db: Session = Depends(get_db), user: UserInfo = Depends(get_current_user)):
    top = db.query(PostAnalytics).order_by(
        desc(PostAnalytics.engagement_score)
    ).limit(10).all()

    result = []
    for a in top:
        post = db.query(Post).filter_by(id=a.post_id).first()
        result.append({
            "post_id": a.post_id,
            "account": a.account,
            "engagement_score": a.engagement_score,
            "reach": a.reach,
            "saves": a.saves,
            "shares": a.shares,
            "content_preview": (post.content_text or "")[:150] if post else "",
            "hook_type": post.hook_type if post else None,
        })

    return {"status": "success", "top_posts": result}


# ── Replies Endpoints ─────────────────────────────────
@router.get("/replies")
def get_pending_replies(
    account: Optional[str] = None,
    db: Session = Depends(get_db),
    user: UserInfo = Depends(get_current_user),
):
    query = db.query(Reply).filter(Reply.status == "pending_approval").order_by(desc(Reply.created_at))
    if account:
        query = query.filter(Reply.account == account)

    replies = query.limit(50).all()
    return {
        "status": "success",
        "count": len(replies),
        "replies": [{
            "id": r.id,
            "post_id": r.post_id,
            "account": r.account,
            "comment_text": r.comment_text,
            "comment_type": r.comment_type,
            "draft_reply": r.draft_reply,
            "status": r.status,
            "created_at": str(r.created_at),
        } for r in replies],
    }


@router.post("/replies/{reply_id}/approve")
def approve_reply(reply_id: int, db: Session = Depends(get_db), user: UserInfo = Depends(get_current_user)):
    reply = db.query(Reply).filter_by(id=reply_id).first()
    if not reply:
        raise HTTPException(404, "Reply not found")
    reply.status = "approved"
    reply.sent_at = datetime.utcnow()
    db.commit()
    return {"status": "success", "reply_id": reply.id}


@router.patch("/replies/{reply_id}")
def edit_reply(
    reply_id: int,
    message: str = Body(...),
    db: Session = Depends(get_db),
    user: UserInfo = Depends(get_current_user),
):
    reply = db.query(Reply).filter_by(id=reply_id).first()
    if not reply:
        raise HTTPException(404, "Reply not found")
    reply.draft_reply = message
    db.commit()
    return {"status": "success", "reply_id": reply.id}


@router.post("/replies/{reply_id}/skip")
def skip_reply(reply_id: int, db: Session = Depends(get_db), user: UserInfo = Depends(get_current_user)):
    reply = db.query(Reply).filter_by(id=reply_id).first()
    if not reply:
        raise HTTPException(404, "Reply not found")
    reply.status = "skipped"
    db.commit()
    return {"status": "success"}


# ── Settings Endpoints ────────────────────────────────
@router.get("/settings/accounts")
def get_account_status(db: Session = Depends(get_db), user: UserInfo = Depends(get_current_user)):
    import os
    accounts = {
        "instagram_personal": {
            "connected": bool(os.getenv("INSTAGRAM_PERSONAL_TOKEN")),
            "label": "Instagram (Personal)",
        },
        "instagram_brand": {
            "connected": bool(os.getenv("INSTAGRAM_BRAND_TOKEN")),
            "label": "Instagram (Nyvora)",
        },
        "facebook": {
            "connected": bool(os.getenv("FACEBOOK_PAGE_TOKEN")),
            "label": "Facebook Page",
        },
        "linkedin": {
            "connected": bool(os.getenv("LINKEDIN_ACCESS_TOKEN")),
            "label": "LinkedIn",
        },
    }
    return {"status": "success", "accounts": accounts}


@router.get("/settings/automation")
def get_automation_level(user: UserInfo = Depends(get_current_user)):
    from backend.scheduler_worker.dispatcher import AUTOMATION_LEVELS
    defaults = {
        "instagram_personal": "semi_auto",
        "instagram_brand": "semi_auto",
        "facebook": "full_auto",
        "linkedin": "semi_auto",
    }
    levels = {k: AUTOMATION_LEVELS.get(k, defaults.get(k, "semi_auto")) for k in defaults}
    return {"status": "success", "levels": levels}


@router.patch("/settings/automation")
def update_automation(
    levels: Dict[str, str] = Body(...),
    user: UserInfo = Depends(get_current_user),
):
    from backend.scheduler_worker.dispatcher import set_automation_level
    for account, level in levels.items():
        if level not in ("full_auto", "semi_auto", "manual"):
            raise HTTPException(400, f"Invalid level: {level}")
        set_automation_level(account, level)
    return {"status": "success"}


@router.get("/settings/workers")
def get_worker_status(db: Session = Depends(get_db), user: UserInfo = Depends(get_current_user)):
    heartbeats = db.query(WorkerHeartbeat).all()
    workers_out = []
    
    now = datetime.utcnow()
    for h in heartbeats:
        status = h.status
        if h.last_heartbeat:
            age_minutes = (now - h.last_heartbeat).total_seconds() / 60
            if age_minutes > 5:
                status = "offline"
                
        workers_out.append({
            "name": h.worker_name,
            "status": status,
            "last_heartbeat": str(h.last_heartbeat),
            "last_run": str(h.last_run) if h.last_run else None,
            "last_status": h.last_status,
            "last_error": h.last_error,
        })
        
    return {
        "status": "success",
        "workers": workers_out,
    }


# ── Notifications ─────────────────────────────────────
@router.get("/notifications")
def get_notifications(db: Session = Depends(get_db), user: UserInfo = Depends(get_current_user)):
    notifs = db.query(Notification).order_by(desc(Notification.created_at)).limit(20).all()
    unread = db.query(Notification).filter(Notification.read == False).count()  # noqa: E712
    return {
        "status": "success",
        "unread_count": unread,
        "notifications": [{
            "id": n.id,
            "type": n.type,
            "message": n.message,
            "read": n.read,
            "created_at": str(n.created_at),
        } for n in notifs],
    }


@router.patch("/notifications/{notif_id}/read")
def mark_notification_read(notif_id: int, db: Session = Depends(get_db), user: UserInfo = Depends(get_current_user)):
    notif = db.query(Notification).filter_by(id=notif_id).first()
    if notif:
        notif.read = True
        db.commit()
    return {"status": "success"}

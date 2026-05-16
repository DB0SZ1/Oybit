"""
Oybit — Pipeline Orchestrator
Executes the full autonomous content pipeline:
  generate → score → guard → render → gate → schedule

Can run individual steps or the full pipeline.
This is the brain that connects all modules together.
"""

import os
from datetime import datetime, timedelta
from typing import Optional
from pathlib import Path

from sqlalchemy.orm import Session

from backend.config import PERSONA_DIR, RENDER_OUTPUT_DIR, OPENROUTER_API_KEY
from backend.db.models import Post, PrePublishGate, SchedulerJob
from backend.persona_engine.prompt_builder import assemble_generation_prompt
from backend.content.generator import generate_content, call_openrouter_raw
from backend.intelligence.scorer import score_post
from backend.brand_voice_guardian.checker import check_brand_voice
from backend.intelligence.mirofish.pre_publish_gate import run_gate
from backend.render_engine.image import generate_image as render_image
from backend.scheduler_worker.queue import SchedulerQueue
from backend.logger import get_logger
from backend.utils.audit_log import log_decision
from backend.safety.sanitizer import sanitize_input
import difflib

logger = get_logger("pipeline")

PERSONA_PATH = os.path.join(PERSONA_DIR, "persona.md")
SIM_LOG_PATH = os.path.join(PERSONA_DIR, "simulation_log.md")

# ── Pipeline Status Enum ──────────────────────────────
PIPELINE_STAGES = [
    "generating",
    "draft",
    "scoring",
    "scored",
    "guarding",
    "approved",
    "rejected",
    "rendering",
    "rendered",
    "gating",
    "gate_passed",
    "gate_failed",
    "gate_delayed",
    "scheduling",
    "scheduled",
    "publishing",
    "published",
    "failed",
]


def _read_persona() -> str:
    """Read persona.md content, return empty string if missing."""
    try:
        with open(PERSONA_PATH, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        logger.warning("persona.md not found — using empty persona")
        return ""


# ═══════════════════════════════════════════════════════
# STEP 1: GENERATE
# ═══════════════════════════════════════════════════════
def step_generate(
    db: Session,
    topic_brief: str,
    platform: str,
    account: str,
    format_type: str = "text",
    dry_run: bool = False,
) -> list[Post]:
    """
    Generate content variants from a topic brief.
    Creates Post records with status='draft'.
    Returns list of created posts.
    """
    logger.info("Pipeline: GENERATE", extra={
        "brief": topic_brief[:100], "platform": platform,
        "account": account, "format": format_type
    })

    # GAP 6.8: Sanitize brief for prompt injection
    safe_topic_brief = sanitize_input(topic_brief)

    # Assemble prompt using persona
    prompt_dict = assemble_generation_prompt(
        persona_path=PERSONA_PATH,
        simulation_log_path=SIM_LOG_PATH,
        topic_brief=safe_topic_brief,
        platform=platform,
        format_type=format_type,
        account=account,
    )

    # Call OpenRouter
    variants = generate_content(prompt_dict, dry_run=dry_run)

    # Create Post records for each variant
    created_posts = []
    for variant_account, content_text in variants.items():
        # If account was specified, only create for that account
        if account and variant_account != account and account != "all":
            continue

        post = Post(
            account=variant_account,
            content_text=content_text,
            status="draft",
            format=format_type,
            topic_pillar=_extract_pillar(safe_topic_brief),
            hook_type=_detect_hook_type(content_text),
            source="system",
            created_at=datetime.utcnow(),
        )
        db.add(post)
        created_posts.append(post)

    db.commit()
    for p in created_posts:
        db.refresh(p)

    log_decision("generation",
                 {"brief": safe_topic_brief[:200], "post_ids": [p.id for p in created_posts],
                  "accounts": [p.account for p in created_posts]},
                 "generated",
                 f"Generated {len(created_posts)} variants from brief")

    return created_posts


# ═══════════════════════════════════════════════════════
# STEP 1.5: NARRATIVE SIMULATION (MiroFish Swarm)
# ═══════════════════════════════════════════════════════
def step_narrative_simulation(db: Session, post: Post) -> Post:
    """
    Run the full MiroFish Swarm Simulation on a drafted variant.
    Updates post with narrative simulation results and confidence.
    """
    logger.info("Pipeline: NARRATIVE SIMULATION", extra={"post_id": post.id})

    try:
        # Run the full swarm simulation on the draft
        sim_result = run_gate(
            rendered_post=post.content_text or "",
            target_account=post.account,
            post_id=str(post.id),
            use_mirofish=True  # Force MiroFish for the early narrative sim
        )
        result_dict = sim_result.__dict__ if hasattr(sim_result, '__dict__') else sim_result
        
        post.narrative_simulation_result = result_dict
        post.narrative_simulation_confidence = result_dict.get("confidence", 0.5)
        post.status = "simulated"
    except Exception as e:
        logger.warning(f"Narrative Simulation failed for post {post.id}: {e}")
        post.narrative_simulation_result = {"error": str(e), "decision": "fail"}
        post.narrative_simulation_confidence = 0.0
        post.status = "simulated"

    db.commit()
    db.refresh(post)

    return post


# ═══════════════════════════════════════════════════════
# STEP 2: SCORE
# ═══════════════════════════════════════════════════════
def step_score(db: Session, post: Post) -> Post:
    """
    Score a draft post using the T/H/P formula.
    Updates post with scores and status='scored'.
    """
    logger.info("Pipeline: SCORE", extra={"post_id": post.id})

    t = _estimate_topicality(post)
    h = _estimate_hook_strength(post.content_text or "")
    p = _estimate_persona_alignment(post.content_text or "")
    total = score_post(t, h, p)  # returns float (sigmoid score)

    post.score_topicality = t
    post.score_hook = h
    post.score_persona = p
    post.score_total = total
    post.status = "scored"

    db.commit()
    db.refresh(post)

    return post


# ═══════════════════════════════════════════════════════
# STEP 3: GUARD (Brand Voice)
# ═══════════════════════════════════════════════════════
def step_guard(db: Session, post: Post) -> Post:
    """
    Run Brand Voice Guardian on a scored post.
    Updates post status='approved' or 'rejected'.
    Returns the post object.
    """
    logger.info("Pipeline: GUARD", extra={"post_id": post.id})

    # GAP 6.2: Duplicate post detection
    # Check similarity against last 10 published/scheduled posts for this account
    recent_posts = db.query(Post).filter(
        Post.account == post.account,
        Post.status.in_(["published", "scheduled", "gate_passed"]),
        Post.id != post.id
    ).order_by(Post.created_at.desc()).limit(10).all()
    
    for rp in recent_posts:
        if not rp.content_text or not post.content_text:
            continue
        similarity = difflib.SequenceMatcher(None, post.content_text.lower(), rp.content_text.lower()).ratio()
        if similarity > 0.8:
            post.status = "rejected"
            db.commit()
            db.refresh(post)
            log_decision("gate", {"post_id": post.id}, "rejected", f"Duplicate post detected. Similarity {similarity:.2f} with post {rp.id}")
            return post

    # GAP 6.3: Hook rotation rule (prevent same hook 3x in a row)
    last_two_posts = db.query(Post).filter(
        Post.account == post.account,
        Post.status.in_(["published", "scheduled", "gate_passed"]),
        Post.hook_type.isnot(None),
        Post.id != post.id
    ).order_by(Post.created_at.desc()).limit(2).all()
    
    if len(last_two_posts) == 2 and all(rp.hook_type == post.hook_type for rp in last_two_posts):
        post.status = "rejected"
        db.commit()
        db.refresh(post)
        log_decision("gate", {"post_id": post.id}, "rejected", f"Hook rotation rule violated. Hook '{post.hook_type}' used 3 times in a row.")
        return post

    result = check_brand_voice(
        text=post.content_text or "",
        platform=_account_to_platform(post.account),
        persona_path=PERSONA_PATH,
        format_type=post.format or "text",
    )

    result_dict = result.__dict__ if hasattr(result, '__dict__') else result

    if result_dict.get("passed", False) or result_dict.get("decision") == "pass":
        post.status = "approved"
        decision = "approved"
    elif result_dict.get("decision") == "near_pass" or result_dict.get("near_pass", False):
        post.status = "approved"  # Near-pass still goes through
        decision = "near_pass"
    else:
        post.status = "rejected"
        decision = "rejected"

    db.commit()
    db.refresh(post)

    log_decision("gate",
                 {"post_id": post.id, "result": result_dict},
                 decision,
                 str(result_dict.get("reason", "")))

    return post


# ═══════════════════════════════════════════════════════
# STEP 4: RENDER
# ═══════════════════════════════════════════════════════
def step_render(db: Session, post: Post) -> Post:
    """
    Render media assets for a post (image/carousel).
    - Carousel: selects template → parses slides → Playwright screenshots
    - Image/Text: generates Pollinations thumbnail
    Updates post.media_urls with rendered file paths.
    """
    logger.info("Pipeline: RENDER", extra={"post_id": post.id, "format": post.format})

    os.makedirs(RENDER_OUTPUT_DIR, exist_ok=True)
    media_urls = []

    try:
        if post.format == "carousel":
            media_urls = _render_carousel(post)
        elif post.format in ("image", "text"):
            image_path = _render_pollinations_image(post)
            if image_path:
                media_urls.append(image_path)
        # Video excluded — Remotion is separate project
    except Exception as e:
        logger.error("Render failed", extra={"post_id": post.id, "error": str(e)})

    post.media_urls = media_urls
    post.status = "rendered" if media_urls else "approved"
    db.commit()
    db.refresh(post)

    return post


def _render_carousel(post: Post) -> list[str]:
    """
    Full carousel rendering pipeline:
    1. Select template based on post attributes
    2. Parse content into slides
    3. Render each slide via Playwright
    Returns list of JPEG file paths.
    """
    from backend.render_engine.templates import (
        select_template, get_template_context, parse_slides_from_content,
    )
    from backend.render_engine.carousel import render_carousel_sync

    # Select the best template
    selection = select_template(
        account=post.account or "instagram_personal",
        hook_type=post.hook_type,
        topic_pillar=post.topic_pillar,
    )
    template_file = selection["template_file"]

    # Parse content into slides
    slides = parse_slides_from_content(post.content_text or "")

    # Build template context
    post_dict = {
        "account": post.account,
        "hook_type": post.hook_type,
        "topic_pillar": post.topic_pillar,
        "cta_text": "Follow for more →",
    }
    context = get_template_context(post_dict, template_key=selection["template_key"])
    context["slide_content"] = [
        {"headline": s["headline"], "body": s["body"]} for s in slides
    ]

    # Output directory for this post's slides
    output_dir = os.path.join(RENDER_OUTPUT_DIR, f"post_{post.id}")
    os.makedirs(output_dir, exist_ok=True)

    logger.info("Rendering carousel", extra={
        "post_id": post.id,
        "template": template_file,
        "template_key": selection["template_key"],
        "slide_count": len(slides),
        "reason": selection["reason"],
    })

    # Render via Playwright
    try:
        paths = render_carousel_sync(template_file, context, output_dir)
        return paths
    except Exception as e:
        logger.warning(f"Carousel render failed, falling back to image: {e}")
        # Fallback: generate a single cover image via Pollinations
        image_path = _render_pollinations_image(post)
        return [image_path] if image_path else []


# ═══════════════════════════════════════════════════════
# STEP 5: GATE (Pre-Publish)
# ═══════════════════════════════════════════════════════
def step_gate(db: Session, post: Post) -> Post:
    """
    Run MiroFish pre-publish gate simulation.
    Returns PASS/FAIL/DELAY decision.
    """
    logger.info("Pipeline: GATE", extra={"post_id": post.id})

    try:
        gate_result = run_gate(
            rendered_post=post.content_text or "",
            target_account=post.account,
            post_id=str(post.id),
        )

        result_dict = gate_result.__dict__ if hasattr(gate_result, '__dict__') else gate_result
    except Exception as e:
        logger.warning("Gate simulation failed — defaulting to PASS", extra={"error": str(e)})
        result_dict = {
            "decision": "pass",
            "confidence": 0.5,
            "source": "score_fallback",
            "predicted_saves": 0,
            "predicted_comments": 0,
            "failure_reason": None,
            "recommended_delay": None,
            "early_learning_signal": {},
        }

    decision = result_dict.get("decision", "pass").lower()
    confidence = result_dict.get("confidence", 0.5)

    # Save gate record
    gate_record = PrePublishGate(
        post_id=str(post.id),
        simulation_result=result_dict,
        confidence_score=confidence,
        failure_reason=result_dict.get("failure_analysis", None),
        early_learning_signal=result_dict,
        created_at=datetime.utcnow(),
    )
    db.add(gate_record)

    # Update post
    post.mirofish_gate_result = decision
    post.mirofish_confidence = confidence
    post.gate_early_signal = result_dict

    if decision == "pass":
        post.status = "gate_passed"
    elif decision == "delay":
        post.status = "gate_delayed"
        delay_minutes = result_dict.get("delay_minutes", 120)
        gate_record.recommended_delay = datetime.utcnow() + timedelta(minutes=delay_minutes)
    else:
        post.status = "gate_failed"

    db.commit()
    db.refresh(post)

    return post


# ═══════════════════════════════════════════════════════
# STEP 6: SCHEDULE
# ═══════════════════════════════════════════════════════
def step_schedule(
    db: Session,
    post: Post,
    scheduled_at: Optional[datetime] = None,
) -> SchedulerJob:
    """
    Add post to the scheduler queue.
    If no time specified, uses smart timing.
    """
    logger.info("Pipeline: SCHEDULE", extra={"post_id": post.id})

    if scheduled_at is None:
        scheduled_at = _get_smart_schedule_time(post.account)

    job = SchedulerJob(
        post_id=post.id,
        account=post.account,
        scheduled_at=scheduled_at,
        status="pending",
        attempts=0,
        created_at=datetime.utcnow(),
    )
    db.add(job)
    post.status = "scheduled"
    post.scheduled_at = scheduled_at
    db.commit()
    db.refresh(job)
    db.refresh(post)

    return job


# ═══════════════════════════════════════════════════════
# FULL PIPELINE — Run Everything
# ═══════════════════════════════════════════════════════
def run_full_pipeline(
    db: Session,
    topic_brief: str,
    platform: str = "linkedin",
    account: str = "linkedin",
    format_type: str = "text",
    dry_run: bool = False,
    auto_schedule: bool = True,
) -> dict:
    """
    Execute the complete pipeline from brief to scheduled post.
    Returns summary of all steps.
    """
    logger.info("Pipeline: FULL RUN", extra={
        "brief": topic_brief[:100], "platform": platform, "account": account
    })

    results = {"steps": [], "posts": [], "final_status": "unknown"}

    try:
        # 1. Generate
        posts = step_generate(db, topic_brief, platform, account, format_type, dry_run)
        results["steps"].append({"step": "generate", "count": len(posts)})

        if not posts:
            results["final_status"] = "no_variants_generated"
            return results

        # 1.5 Narrative Simulation
        for post in posts:
            step_narrative_simulation(db, post)
        results["steps"].append({"step": "narrative_simulation", "count": len(posts)})

        # 2. Score all variants
        for post in posts:
            step_score(db, post)
        results["steps"].append({"step": "score", "count": len(posts)})

        # 3. Select top post by score
        # Incorporate narrative simulation confidence into the final selection logic
        def get_weighted_score(p):
            base_score = p.score_total or 0
            sim_conf = p.narrative_simulation_confidence or 0.5
            return (base_score * 0.7) + (sim_conf * 0.3)

        best_post = max(posts, key=get_weighted_score)
        results["steps"].append({"step": "selected", "post_id": best_post.id, "score": best_post.score_total, "sim_confidence": best_post.narrative_simulation_confidence})

        # 4. Guardian check
        guard_result = step_guard(db, best_post)
        results["steps"].append({"step": "guard", "decision": guard_result["decision"]})

        if guard_result["decision"] == "rejected":
            # Try next best post
            remaining = [p for p in posts if p.id != best_post.id and p.status != "rejected"]
            if remaining:
                best_post = max(remaining, key=lambda p: p.score_total or 0)
                guard_result = step_guard(db, best_post)
                results["steps"].append({"step": "guard_retry", "decision": guard_result["decision"]})

        if best_post.status == "rejected":
            results["final_status"] = "rejected_by_guardian"
            return results

        # 5. Render (image/carousel)
        if format_type != "text":
            step_render(db, best_post)
            results["steps"].append({"step": "render", "media_count": len(best_post.media_urls or [])})

        # 6. Gate
        gate_result = step_gate(db, best_post)
        results["steps"].append({"step": "gate", "decision": gate_result["decision"]})

        if gate_result["decision"] == "fail":
            results["final_status"] = "gate_failed"
            return results

        # 7. Schedule (if auto)
        if auto_schedule and best_post.status == "gate_passed":
            job = step_schedule(db, best_post)
            results["steps"].append({"step": "schedule", "job_id": job.id, "scheduled_at": str(job.scheduled_at)})
            results["final_status"] = "scheduled"
        else:
            results["final_status"] = best_post.status

        results["posts"].append({
            "id": best_post.id,
            "account": best_post.account,
            "status": best_post.status,
            "score": best_post.score_total,
            "content_preview": (best_post.content_text or "")[:200],
        })

    except Exception as e:
        logger.error("Pipeline failed", extra={"error": str(e)})
        results["final_status"] = "error"
        results["error"] = str(e)

    return results


# ═══════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════
def _account_to_platform(account: str) -> str:
    mapping = {
        "instagram_personal": "instagram",
        "instagram_brand": "instagram",
        "facebook": "facebook",
        "linkedin": "linkedin",
    }
    return mapping.get(account, account)


def _extract_pillar(brief: str) -> str:
    """Extract content pillar from topic brief text."""
    brief_lower = brief.lower()
    if any(w in brief_lower for w in ["build", "ship", "code", "product", "feature"]):
        return "building_in_public"
    elif any(w in brief_lower for w in ["africa", "nigeria", "abuja", "lagos"]):
        return "african_founder"
    elif any(w in brief_lower for w in ["security", "system", "architecture", "api"]):
        return "technical_systems"
    elif any(w in brief_lower for w in ["learn", "lesson", "mistake", "decision"]):
        return "founder_lessons"
    return "general"


def _detect_hook_type(text: str) -> str:
    """Detect hook type from content text."""
    if not text:
        return "unknown"
    first_line = text.strip().split("\n")[0].lower()
    if "?" in first_line:
        return "question"
    elif any(w in first_line for w in ["i ", "my ", "we "]):
        return "personal_story"
    elif any(c.isdigit() for c in first_line):
        return "specific_number"
    elif any(w in first_line for w in ["don't", "stop", "never", "wrong"]):
        return "contradiction"
    return "statement"


def _estimate_topicality(post: Post) -> float:
    """Rough topicality estimate. In production, uses MiroFish trend data."""
    return 0.6  # Baseline — updated by MiroFish worker


def _estimate_hook_strength(text: str) -> float:
    """Rough hook strength estimate based on heuristics."""
    if not text:
        return 0.3
    first_line = text.strip().split("\n")[0]
    score = 0.5
    if len(first_line) < 80:
        score += 0.1  # Short hooks perform better
    if "?" in first_line:
        score += 0.1
    if any(c.isdigit() for c in first_line):
        score += 0.1
    if first_line[0:1].isupper() and not first_line.startswith("I "):
        score += 0.05
    return min(score, 1.0)


def _estimate_persona_alignment(text: str) -> float:
    """Rough persona alignment. In production, uses semantic similarity."""
    persona = _read_persona()
    if not persona:
        return 0.5
    # Simple keyword overlap heuristic
    persona_words = set(persona.lower().split())
    text_words = set(text.lower().split())
    overlap = len(persona_words & text_words)
    return min(overlap / max(len(text_words), 1) * 5, 1.0)


def _render_pollinations_image(post: Post) -> Optional[str]:
    """Generate a thumbnail image via Pollinations.ai."""
    try:
        content_snippet = (post.content_text or "")[:100]
        prompt = f"Minimalist tech blog thumbnail, dark theme, abstract geometric shapes, topic: {content_snippet}"
        
        # Use the existing image renderer
        output_path = os.path.join(RENDER_OUTPUT_DIR, f"post_{post.id}_thumb.jpg")
        result = render_image(prompt=prompt, output_path=output_path)
        if result and os.path.exists(result):
            return result
        return None
    except Exception as e:
        logger.warning("Image render failed", extra={"post_id": post.id, "error": str(e)})
        return None


def _get_smart_schedule_time(account: str) -> datetime:
    """Get optimal posting time based on account and platform best practices."""
    now = datetime.utcnow()
    # WAT is UTC+1
    wat_hour = (now.hour + 1) % 24

    # Optimal hours per platform (in WAT)
    optimal_hours = {
        "linkedin": [8, 9, 10, 12],          # Weekday mornings
        "instagram_personal": [12, 18, 20],   # Lunch + evening
        "instagram_brand": [10, 14, 17],      # Business hours
        "facebook": [13, 15, 19],             # Afternoon + evening
    }

    target_hours = optimal_hours.get(account, [12])

    # Find next optimal slot
    for h in target_hours:
        # Convert WAT target to UTC
        utc_hour = (h - 1) % 24
        target = now.replace(hour=utc_hour, minute=0, second=0, microsecond=0)
        if target > now:
            return target

    # All today's slots passed — schedule for tomorrow's first slot
    first_hour_utc = (target_hours[0] - 1) % 24
    tomorrow = now + timedelta(days=1)
    return tomorrow.replace(hour=first_hour_utc, minute=0, second=0, microsecond=0)

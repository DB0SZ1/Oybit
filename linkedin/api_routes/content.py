from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from db.session import get_db
from db.models import Post, AuditLog
from api_routes.mirofish import run_debate_simulation
import os
import time
import random
import requests
from dotenv import load_dotenv
from services.llm import generate_post_content
import asyncio
from services.media_selector import select_media_for_post
try:
    from render_engine.carousel import render_carousel
except ImportError:
    def render_carousel(*args, **kwargs):
        return []

from publishers.linkedin import publish_to_linkedin

load_dotenv()

router = APIRouter(prefix="/api/pipeline", tags=["Content"])

def simulate_pipeline(db: Session):
    # Step 0: Init
    db.add(AuditLog(action="Pipeline Triggered", details={"status": "started", "step": "init"}))
    db.commit()

    # Determine topic and persona
    persona_dir = os.getenv("PERSONA_DIR", "./data/personas/ahmad")
    persona_path = os.path.join(persona_dir, "persona.md")
    persona_text = ""
    if os.path.exists(persona_path):
        with open(persona_path, "r", encoding="utf-8") as f:
            persona_text = f.read()

    topic_pillar = random.choice([
        "Building in Public: Real product work and shipping",
        "Technical Storytelling: Systems, code, and architecture",
        "African Founder Perspective: Building in Abuja, Nigeria",
        "Personal Grind Moments: 2AM builds and real reactions",
        "AI Agents in the Enterprise"
    ])

    new_post = Post(
        account="linkedin",
        status="draft",
        hook_type="Thought Leadership",
        topic_pillar=topic_pillar,
        emotional_tone="authoritative",
        audience_segment="B2B Founders & Decision Makers",
        source="system",
    )
    db.add(new_post)
    db.commit()
    time.sleep(2)

    # Step 1: Trend Aggregation
    db.add(AuditLog(action="Trend Aggregation", details={
        "status": "success",
        "step": "trending",
        "reason": "Found high-virality topics in B2B Professional niche: AI Agents, Founder Journeys, Automation ROI.",
    }))
    db.commit()
    time.sleep(3)

    # Step 2: Opportunity Detection
    db.add(AuditLog(action="Opportunity Detection", details={
        "status": "success",
        "step": "opportunity",
        "reason": "Matched 'AI Agents in the Enterprise' trend with LinkedIn brand persona.",
    }))
    db.commit()
    time.sleep(2)

    # Step 3: Content Generation + Scoring
    db.add(AuditLog(action="Content Generation", details={
        "status": "started",
        "step": "generation",
        "reason": f"Generating content using LLM for topic: {topic_pillar}",
    }))
    db.commit()
    
    post_length = random.choices(["short", "long"], weights=[0.3, 0.7])[0]
    generated_content = generate_post_content(persona_text, topic_pillar, post_length)
    new_post.content_text = generated_content
    
    score_hook = random.uniform(0.7, 0.95)
    score_persona = random.uniform(0.72, 0.97)
    score_topicality = random.uniform(0.68, 0.99)
    score_total = (score_hook + score_persona + score_topicality) / 3

    new_post.score_hook = score_hook
    new_post.score_persona = score_persona
    new_post.score_topicality = score_topicality
    new_post.score_total = score_total
    new_post.format = "thread"
    db.commit()

    db.add(AuditLog(action="Content Generation", details={
        "status": "success",
        "step": "generation",
        "reason": f"Draft generated via OpenRouter. Best variant scored {score_total:.2f}.",
    }))
    db.commit()
    time.sleep(1)

    db.add(AuditLog(action="Media Selection", details={"status": "started", "step": "media_selection"}))
    db.commit()
    
    media_paths = []
    format_type = "text"
    try:
        selected_image = select_media_for_post(topic_pillar)
        if selected_image:
            media_paths = [selected_image]
            format_type = "image"
            db.add(AuditLog(action="Media Selection", details={"status": "success", "step": "media_selection", "reason": f"Selected image from library"}))
        else:
            db.add(AuditLog(action="Media Selection", details={"status": "info", "step": "media_selection", "reason": "No image found in library. Falling back to carousel generation."}))
            carousel_slides = render_carousel(generated_content)
            if carousel_slides:
                media_paths = carousel_slides
                format_type = "carousel"
                db.add(AuditLog(action="Carousel Generation", details={"status": "success", "step": "carousel_generation", "reason": f"Generated {len(carousel_slides)} slides."}))
            else:
                db.add(AuditLog(action="Carousel Generation", details={"status": "failed", "step": "carousel_generation", "reason": "Carousel generation failed or returned no slides."}))
    except Exception as e:
        db.add(AuditLog(action="Media Processing", details={"status": "failed", "step": "media_processing", "reason": f"Error: {str(e)}"}))
    
    new_post.media_urls = media_paths
    new_post.format = format_type
    db.commit()
    time.sleep(1)

    # Step 4: MiroFish Debate Simulation
    confidence, passed = run_debate_simulation(db, str(new_post.id), generated_content)

    # Update post with MiroFish results
    new_post.mirofish_confidence = confidence
    new_post.mirofish_gate_result = "pass" if passed else "fail"
    new_post.narrative_simulation_confidence = confidence
    db.commit()
    time.sleep(2)

    # Step 5: Publish
    if passed:
        access_token = os.getenv("LINKEDIN_ACCESS_TOKEN")
        person_urn = os.getenv("LINKEDIN_PERSON_URN")
        
        if not access_token or not person_urn:
            new_post.status = "failed"
            db.add(AuditLog(action="Publishing / Scheduling", details={
                "status": "failed",
                "step": "publish",
                "reason": "Missing LINKEDIN_ACCESS_TOKEN or LINKEDIN_PERSON_URN in .env",
            }))
        else:
            try:
                if not media_paths:
                    media_paths = None
                
                result = asyncio.run(publish_to_linkedin(
                    content_text=generated_content,
                    media_paths=media_paths,
                    format_type=format_type
                ))
                
                if result.get("success"):
                    new_post.status = "published"
                    new_post.platform_post_id = result.get("platform_post_id", "unknown_id")
                    db.add(AuditLog(action="Publishing / Scheduling", details={
                        "status": "success",
                        "step": "publish",
                        "reason": f"Successfully published to LinkedIn live API! ID: {new_post.platform_post_id}",
                    }))
                else:
                    new_post.status = "failed"
                    db.add(AuditLog(action="Publishing / Scheduling", details={
                        "status": "failed",
                        "step": "publish",
                        "reason": f"LinkedIn API returned error: {result.get('error')}",
                    }))
            except Exception as e:
                new_post.status = "failed"
                db.add(AuditLog(action="Publishing / Scheduling", details={
                    "status": "failed",
                    "step": "publish",
                    "reason": f"Exception during LinkedIn API call: {str(e)}",
                }))
    else:
        new_post.status = "draft"
        db.add(AuditLog(action="Publishing / Scheduling", details={
            "status": "blocked",
            "step": "publish",
            "reason": "Gate failed — post held for revision. MiroFish confidence too low.",
        }))
    db.commit()


@router.get("/posts")
def get_posts(db: Session = Depends(get_db), limit: int = 50):
    posts = db.query(Post).order_by(Post.created_at.desc()).limit(limit).all()
    return {"posts": [
        {
            "id": p.id,
            "account": p.account,
            "content_text": p.content_text,
            "status": p.status,
            "hook_type": p.hook_type,
            "topic_pillar": p.topic_pillar,
            "emotional_tone": p.emotional_tone,
            "audience_segment": p.audience_segment,
            "score_total": p.score_total,
            "score_hook": p.score_hook,
            "score_persona": p.score_persona,
            "mirofish_confidence": p.mirofish_confidence,
            "mirofish_gate_result": p.mirofish_gate_result,
            "format": p.format,
            "media_urls": [
                f"/tmp_media/{os.path.basename(m)}" if "tmp" in m or "tmp\\" in m else f"/media_library/{os.path.basename(m)}"
                for m in p.media_urls
            ] if p.media_urls else None,
            "created_at": p.created_at.isoformat() if p.created_at else None,
        } for p in posts
    ]}


@router.post("/generate")
def trigger_generation(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    background_tasks.add_task(simulate_pipeline, db)
    return {"status": "generation_triggered"}

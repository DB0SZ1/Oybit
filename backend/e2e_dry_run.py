"""
Oybit — End-to-End Dry Run Script
Tests the full lifecycle of a post without publishing or calling expensive APIs.
Flow: Generate → Score → Guard → Render → Gate → Schedule
"""
import os
import logging
from datetime import datetime
from sqlalchemy.orm import Session

# Setup logging before importing backend modules
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger("e2e_test")

from backend.db.session import SessionLocal, engine
from backend.db.base import Base
from backend.db.models import Post
from backend.api.pipeline import (
    step_generate,
    step_score,
    step_guard,
    step_render,
    step_gate,
    step_schedule
)

def run_e2e_test():
    logger.info("Starting E2E Dry-Run Test...")
    
    # 1. Init DB
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    try:
        # 2. GENERATE
        logger.info("\n=== STAGE 1: GENERATE ===")
        topic_brief = "Why traditional REST APIs are slowing down frontend teams. The shift to GraphQL and tRPC."
        posts = step_generate(
            db=db,
            topic_brief=topic_brief,
            platform="linkedin",
            account="linkedin",
            format_type="carousel"
        )
        
        if not posts:
            logger.error("Failed to generate posts!")
            return
            
        post = posts[0]
        logger.info(f"Created Post ID {post.id} with status '{post.status}'")
        logger.info(f"Content excerpt: {post.content_text[:100]}...")
        
        # 3. SCORE
        logger.info("\n=== STAGE 2: SCORE ===")
        post = step_score(db, post)
        logger.info(f"Scored! Hook: {post.score_hook}, Topic: {post.score_topicality}, Persona: {post.score_persona}")
        logger.info(f"Status is now '{post.status}'")
        
        # 4. GUARD
        logger.info("\n=== STAGE 3: GUARD ===")
        # We manually inject a hard stop word to test the guardian, or just let it pass
        post = step_guard(db, post)
        logger.info(f"Guardian check complete. Status is now '{post.status}'")
        if post.status == "rejected":
            logger.warning("Post was rejected by Guardian. Force-approving for the rest of the pipeline test.")
            post.status = "approved"
            db.commit()
            
        # 5. RENDER
        logger.info("\n=== STAGE 4: RENDER ===")
        # Note: step_render will try to call Pollinations/Playwright. 
        # We'll let it run. If Playwright isn't installed, it falls back to Pollinations.
        post = step_render(db, post)
        logger.info(f"Render complete. Status is now '{post.status}'")
        logger.info(f"Media URLs: {post.media_urls}")
        
        # 6. GATE (MiroFish)
        logger.info("\n=== STAGE 5: GATE (MiroFish) ===")
        # Simulate the gate. MiroFish simulation runner requires OpenRouter API key.
        # If no key, it should fallback gracefully.
        post = step_gate(db, post)
        logger.info(f"Gate complete. Decision: {post.mirofish_gate_result} (Confidence: {post.mirofish_confidence})")
        logger.info(f"Status is now '{post.status}'")
        
        # 7. SCHEDULE
        logger.info("\n=== STAGE 6: SCHEDULE ===")
        # If gate passed, it should schedule. If delayed/failed, we force it for the test.
        if post.status not in ["gate_passed", "approved", "rendered"]:
            logger.info("Force approving post for scheduling test...")
            post.status = "approved"
            db.commit()
            
        job = step_schedule(db, post)
        logger.info(f"Scheduling complete. Job ID: {job.id}, Status: {job.status}")
        if job.scheduled_at:
            logger.info(f"Scheduled for: {job.scheduled_at}")
        else:
            logger.warning("Post was not scheduled (might be in drafts).")
            
        logger.info("\n=== E2E TEST COMPLETED SUCCESSFULLY ===")
        
    except Exception as e:
        logger.exception(f"E2E Test failed with error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    if not os.getenv("OPENROUTER_API_KEY"):
        logger.error("OPENROUTER_API_KEY is not set in the environment. E2E test requires a real API key.")
        exit(1)
        
    run_e2e_test()

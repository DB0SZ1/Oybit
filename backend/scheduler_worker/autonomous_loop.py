"""
Autonomous Orchestrator Loop — Agent A
Coordinates the Opportunity Detection → Content Generation → Publishing loop.
"""

import os
import json
import logging
from datetime import datetime
from sqlalchemy.orm import Session
import asyncio

from backend.db.session import SessionLocal
from backend.db.models import TrendSignal, Post, PostAnalytics
from backend.config import PERSONA_DIR
from backend.intelligence.mirofish.narrative_forecaster import run_daily_forecast
from backend.intelligence.opportunity_detector import detect_opportunities
from backend.api.pipeline import run_full_pipeline

logger = logging.getLogger(__name__)
PERSONA_PATH = os.path.join(PERSONA_DIR, "persona.md")


def _extract_niche_from_persona() -> list:
    """Extract niche/industry keywords from persona.md for trend scanning."""
    default_keywords = ["startup", "saas", "tech"]
    if not os.path.exists(PERSONA_PATH):
        return default_keywords

    try:
        with open(PERSONA_PATH, "r", encoding="utf-8") as f:
            content = f.read()

        # Simple extraction logic: look for "Niche:" or "Industry:"
        import re
        match = re.search(r'(?:Niche|Industry|Topics)[:\s]+(.+)', content, re.IGNORECASE)
        if match:
            words = [w.strip() for w in match.group(1).split(',')]
            return words if words else default_keywords
        return default_keywords
    except Exception as e:
        logger.warning(f"Failed to extract niche from persona: {e}")
        return default_keywords


def run_opportunity_polling():
    """
    Run the autonomous opportunity polling loop:
    1. Extract niche from persona
    2. Run MiroFish forecast to find trends
    3. Filter through Opportunity Detector
    4. Save to TrendSignal DB (handle duplicates/recurring)
    5. Trigger full pipeline for new/recurring trends
    """
    logger.info("Starting Autonomous Opportunity Polling")
    db = SessionLocal()
    try:
        keywords = _extract_niche_from_persona()
        logger.info(f"Polling trends for keywords: {keywords}")

        # Run MiroFish forecast
        forecast_result = run_daily_forecast(keywords=keywords)
        narratives = forecast_result.get("narratives", [])

        if not narratives:
            logger.info("No narratives found in forecast.")
            return

        # Filter through Opportunity Detector (persona lens + hard stops)
        approved_briefs = detect_opportunities(
            narratives=narratives,
            persona_path=PERSONA_PATH,
            relevance_threshold=0.6,
        )

        for brief in approved_briefs:
            _process_approved_brief(db, brief)

    except Exception as e:
        logger.error(f"Error in opportunity polling loop: {e}", exc_info=True)
    finally:
        db.close()


def _process_approved_brief(db: Session, brief):
    """Process an approved brief, handle duplicate tracking, and trigger pipeline."""
    # Check if this topic already exists in TrendSignal
    existing_trend = db.query(TrendSignal).filter(TrendSignal.topic == brief.topic).first()

    status = "new"
    recurring_context = None

    if existing_trend:
        # If the trend was already handled recently, we might skip it or mark recurring
        if existing_trend.status in ["used", "recurring"]:
            # If it trended before and is trending again, we mark it recurring
            status = "recurring"
            recurring_context = f"This topic previously trended on {existing_trend.collected_at}. Focus on what's new: {brief.angle}"
            logger.info(f"Recurring trend detected: {brief.topic}")
        else:
            logger.info(f"Trend already in progress: {brief.topic}")
            return
    else:
        # Create new trend signal
        existing_trend = TrendSignal(
            source="mirofish_forecast",
            topic=brief.topic,
            raw_data={"angle": brief.angle, "dna_element": brief.dna_element, "timing": brief.timing},
        )
        db.add(existing_trend)
        db.flush()

    existing_trend.status = status
    existing_trend.recurring_style_context = recurring_context
    db.commit()

    # Trigger Content Generation Pipeline
    full_brief_text = f"Topic: {brief.topic}\nAngle: {brief.angle}\nDNA Element: {brief.dna_element}"
    if recurring_context:
        full_brief_text += f"\nNote: {recurring_context}"

    # We select the primary target account (just pick the first one, pipeline handles targeting)
    primary_account = brief.target_accounts[0] if brief.target_accounts else "linkedin"

    logger.info(f"Triggering pipeline for trend: {brief.topic}")
    
    try:
        # We need an event loop if we are calling async functions, but run_full_pipeline is mostly sync
        # Wait, run_full_pipeline uses step_narrative_simulation which calls run_gate which creates an event loop.
        # Since we are running in a worker thread, this is fine.
        pipeline_result = run_full_pipeline(
            db=db,
            topic_brief=full_brief_text,
            platform=primary_account.split('_')[0],
            account=primary_account,
            format_type="text",
            auto_schedule=True,
        )
        
        if pipeline_result.get("final_status") == "scheduled":
            existing_trend.status = "used"
            db.commit()
            logger.info(f"Pipeline successfully scheduled content for trend: {brief.topic}")
        else:
            logger.warning(f"Pipeline did not finish scheduling for trend: {brief.topic}. Status: {pipeline_result.get('final_status')}")
            
    except Exception as e:
        logger.error(f"Failed to run pipeline for trend {brief.topic}: {e}")


def run_post_verification():
    """
    Check if scheduled posts that have passed their published_at time
    are actually live on the platform. If not (e.g. deleted by user),
    log a negative learning signal.
    """
    logger.info("Starting Post Verification Loop")
    db = SessionLocal()
    try:
        # Find posts that are marked published but not verified
        unverified_posts = db.query(Post).filter(
            Post.status == "published",
            Post.post_publish_verified == False
        ).all()

        for post in unverified_posts:
            # Here we would normally make an HTTP request to platform APIs using post.platform_post_id
            # to verify if the post still exists.
            # For now, we simulate the check.
            if not post.platform_post_id:
                logger.warning(f"Post {post.id} is marked published but has no platform_post_id. Skipping.")
                continue

            # Simulated Verification Logic
            # In production, call e.g., LinkedIn API GET /v2/ugcPosts/{id}
            post_exists_on_platform = _simulate_platform_verify(post.account, post.platform_post_id)

            if not post_exists_on_platform:
                logger.info(f"Post {post.id} ({post.platform_post_id}) not found on platform. Likely deleted.")
                # Mark as deleted/negative learning signal
                post.status = "deleted"
                
                # Create a negative analytic signal
                analytics = db.query(PostAnalytics).filter(PostAnalytics.post_id == post.id).first()
                if not analytics:
                    analytics = PostAnalytics(post_id=post.id, account=post.account)
                    db.add(analytics)
                
                analytics.engagement_score = -1.0
                analytics.publish_error = "Post was deleted by user after publishing."
                post.post_publish_verified = True
            else:
                logger.info(f"Post {post.id} verified as live.")
                post.post_publish_verified = True

            db.commit()

    except Exception as e:
        logger.error(f"Error in post verification loop: {e}")
    finally:
        db.close()


def _simulate_platform_verify(account: str, platform_post_id: str) -> bool:
    """Mock platform verification. Returns True if post exists."""
    # We'll assume the post exists unless it has 'deleted' in the ID (for testing)
    if "deleted" in platform_post_id.lower():
        return False
    return True

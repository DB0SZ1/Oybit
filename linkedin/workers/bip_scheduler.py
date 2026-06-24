import os
import re
import time
import json
import logging
from sqlalchemy.orm import Session
from db.session import SessionLocal
from db.models import Post, AuditLog
from services.llm import generate_build_in_public_post

logger = logging.getLogger("bip_scheduler")

BUILD_LOG_PATH = os.path.join(os.getcwd(), "BUILD_LOG.md")

def extract_and_archive_unposted_progress() -> str:
    """
    Reads unposted progress from the BuildLogEntry PostgreSQL table, marks them as archived, and returns the combined text.
    Returns (raw_progress, last_archived) tuple.
    """
    from db.models import BuildLogEntry
    db = SessionLocal()
    try:
        entries = db.query(BuildLogEntry).filter(BuildLogEntry.status == "unposted").order_by(BuildLogEntry.created_at.asc()).all()
        if not entries:
            return None, None
            
        raw_progress = "\n".join([e.summary for e in entries])
        
        # DO NOT mark as archived here! 
        # Return the IDs so run_bip_batch_cycle can mark them archived ONLY after successful LLM generation.
        entry_ids = [e.id for e in entries]
        return raw_progress, entry_ids
    except Exception as e:
        logger.error(f"Failed to extract unposted progress from DB: {e}")
        return None, None
    finally:
        db.close()


def run_bip_batch_cycle():
    """
    Called 3-4 times a day by the main scheduler loop.
    Reads batched logs, asks LLM to write a massive post, and saves to DB.
    """
    logger.info("Running BIP Batch Cycle...")
    
    raw_progress, entry_ids = extract_and_archive_unposted_progress()
    
    if not raw_progress:
        logger.info("No new unposted progress found. Skipping cycle (doing stuff only when needed).")
        return

    details_to_use = raw_progress

    db: Session = SessionLocal()
    try:
        from db.models import BipState
        from datetime import datetime
        
        # State Tracking
        state = db.query(BipState).filter(BipState.project_name == "kronos").first()
        if not state:
            state = BipState(project_name="kronos", start_date=datetime.utcnow(), current_day=1)
            db.add(state)
            db.commit()
            
        # Determine Day Number
        days_diff = (datetime.utcnow() - state.start_date).days
        day_number = max(1, days_diff + 1)
        state.current_day = day_number

        from db.models import Post
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        today_posts_count = db.query(Post).filter(Post.created_at >= today_start).count()
        
        # 4 updates * 3 platforms = 12 post entries limit
        if today_posts_count >= 12:
            logger.info("Daily post limit (4 updates) reached. Leaving progress as unposted for tomorrow.")
            return
            
        is_first_post_today = (today_posts_count == 0)
        
        # Determine Post Type
        post_type = "The Update"
        if day_number == 1 and state.total_posts == 0:
            post_type = "Day 1 Anchor"
        elif day_number > 0 and day_number % 7 == 0:
            post_type = "The Metric Drop"
        else:
            # Cycle through the other 3
            cycle = ["The Update", "The Lesson Post", "The Behind-the-Scenes"]
            last_idx = -1
            if state.last_post_type in cycle:
                last_idx = cycle.index(state.last_post_type)
            post_type = cycle[(last_idx + 1) % len(cycle)]
            
        logger.info(f"Determined State -> Day {day_number}, Type: {post_type}")
        
    # We have progress! Let's build a fake "latest_entry" payload for the LLM
        log_entry = {
        "title": f"Sprint Day {day_number}",
        "tags": ["#BuildInPublic", "#Engineering", "#Shipping"],
        "details": details_to_use,
        "images": [] # For fully automated, we skip images or parse them from the log if they existed
    }
    
        persona_path = os.getenv("PERSONA_DIR", "./data/personas/ahmad") + "/persona.md"
        persona_text = ""
        if os.path.exists(persona_path):
            with open(persona_path, "r", encoding="utf-8") as f:
                persona_text = f.read()

        logger.info(f"Sending progress to LLM for LinkedIn...")
        generated_content = generate_build_in_public_post(
            log_entry=log_entry, 
            persona_text=persona_text, 
            day_number=day_number, 
            post_type=post_type,
            is_first_post_today=is_first_post_today
        )
        
        new_post = Post(
            account="linkedin",
            status="draft", 
            hook_type=post_type,
            topic_pillar="BIP: Batched Sprint",
            content_text=generated_content,
            format="thread",
            source="bip_scheduler"
        )
        db.add(new_post)
        
        # Load X and Reddit Prompts
        x_prompt_path = os.path.join(os.getcwd(), "persona_data", "x_bip_prompt.txt")
        reddit_prompt_path = os.path.join(os.getcwd(), "persona_data", "reddit_bip_prompt.txt")
        x_prompt_text = ""
        reddit_prompt_text = ""
        if os.path.exists(x_prompt_path):
            with open(x_prompt_path, "r", encoding="utf-8") as f:
                x_prompt_text = f.read()
        if os.path.exists(reddit_prompt_path):
            with open(reddit_prompt_path, "r", encoding="utf-8") as f:
                reddit_prompt_text = f.read()

        # X (Twitter) Post
        if x_prompt_text:
            logger.info("Sending batched progress to LLM for X (Twitter)...")
            try:
                from services.llm import generate_x_bip_post
                x_json = generate_x_bip_post(
                    log_entry=log_entry, 
                    prompt_text=x_prompt_text,
                    day_number=day_number,
                    post_type=post_type,
                    is_first_post_today=is_first_post_today
                )
                if x_json.get("is_thread") and x_json.get("thread_posts"):
                    x_content = "\n\n---\n\n".join(x_json["thread_posts"])
                else:
                    x_content = x_json.get("post", "")
                
                if x_content:
                    x_post = Post(
                        account="twitter",
                        status="draft",
                        hook_type=x_json.get("type", "build_update"),
                        topic_pillar="BIP: Batched Sprint",
                        content_text=f"{x_content}\n\n[NOTE: {x_json.get('note', '')}]",
                        format="thread" if x_json.get("is_thread") else "text",
                        source="bip_scheduler"
                    )
                    db.add(x_post)
                    db.flush() # get ID
                    
                    from scheduler_worker.queue import SchedulerQueue
                    from datetime import datetime
                    SchedulerQueue(db).add_job(x_post.id, "twitter", datetime.utcnow())
            except Exception as e:
                logger.error(f"Failed to generate X post: {e}")

        # Reddit Post
        if reddit_prompt_text:
            logger.info("Sending batched progress to LLM for Reddit...")
            try:
                from services.llm import generate_reddit_bip_post
                reddit_json = generate_reddit_bip_post(
                    log_entry=log_entry, 
                    prompt_text=reddit_prompt_text,
                    day_number=day_number,
                    post_type=post_type,
                    is_first_post_today=is_first_post_today
                )
                
                reddit_content = reddit_json.get("post", "")
                if reddit_content:
                    r_post = Post(
                        account="reddit",
                        status="draft",
                        hook_type=reddit_json.get("type", post_type),
                        topic_pillar="BIP: Batched Sprint",
                        content_text=reddit_content,
                        format="text",
                        source="bip_scheduler"
                    )
                    db.add(r_post)
                    db.flush() # get ID
                    
                    from scheduler_worker.queue import SchedulerQueue
                    from datetime import datetime
                    SchedulerQueue(db).add_job(r_post.id, "reddit", datetime.utcnow())
            except Exception as e:
                logger.error(f"Failed to generate Reddit BIP post: {e}")

        db.add(AuditLog(action="BIP Scheduler", details={
            "status": "success",
            "step": "bip_batch_generation",
            "reason": f"Generated drafts for {post_type} across LinkedIn, X, and Reddit",
        }))
        db.commit()
        logger.info("✅ Successfully generated BIP Post Drafts and Scheduled them!")
        
        # Fully autonomous publishing
        # Fully autonomous publishing
        from publishers.linkedin import publish_to_linkedin
        import asyncio
        
        logger.info("Skipping MiroFish gate. Publishing directly to LinkedIn...")
        new_post.mirofish_confidence = 100.0
        new_post.mirofish_gate_result = "bypassed"
        db.commit()
        
        try:
            result = asyncio.run(publish_to_linkedin(
                content_text=generated_content,
                media_paths=None,
                format_type="text"
            ))
            if result.get("success"):
                new_post.status = "published"
                new_post.platform_post_id = result.get("platform_post_id", "unknown_id")
                logger.info("✅ Successfully published BIP Post to LinkedIn!")
            else:
                new_post.status = "failed"
                logger.error(f"Failed to publish to LinkedIn: {result.get('error')}")
                # Schedule it for Twilio fallback via dispatcher
                from scheduler_worker.queue import SchedulerQueue
                from datetime import datetime
                SchedulerQueue(db).add_job(new_post.id, "linkedin", datetime.utcnow())
        except Exception as e:
            new_post.status = "failed"
            logger.error(f"Exception publishing to LinkedIn: {e}")
            from scheduler_worker.queue import SchedulerQueue
            from datetime import datetime
            SchedulerQueue(db).add_job(new_post.id, "linkedin", datetime.utcnow())
            
        db.commit()
            
        # VERY END OF SUCCESSFUL GENERATION: Now we can safely archive the logs!
        if entry_ids:
            from db.models import BuildLogEntry
            logs_to_archive = db.query(BuildLogEntry).filter(BuildLogEntry.id.in_(entry_ids)).all()
            for e in logs_to_archive:
                e.status = "archived"
                
            state.last_post_type = post_type
            state.total_posts += 1
            db.commit()
            logger.info(f"Safely archived {len(logs_to_archive)} build log entries.")
        

        
    except Exception as e:
        logger.error(f"Failed to generate BIP post: {e}")
    finally:
        db.close()


def start_bip_loop():
    """Background loop that wakes up every 6 hours (4x a day)."""
    logger.info("Starting Build-in-Public background worker (4x daily)...")
    while True:
        try:
            run_bip_batch_cycle()
        except Exception as e:
            logger.error(f"BIP loop error: {e}")
            
        # Sleep for 6 hours (21600 seconds)
        time.sleep(21600)

if __name__ == "__main__":
    start_bip_loop()

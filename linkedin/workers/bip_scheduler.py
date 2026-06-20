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
    Reads the UNPOSTED PROGRESS section, extracts the text, and moves it to ARCHIVED PROGRESS.
    Returns the extracted text, or None if empty.
    """
    if not os.path.exists(BUILD_LOG_PATH):
        return None

    with open(BUILD_LOG_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    unposted_marker = "## UNPOSTED PROGRESS"
    archived_marker = "## ARCHIVED PROGRESS"
    
    if unposted_marker not in content or archived_marker not in content:
        return None
        
    parts = content.split(unposted_marker, 1)
    top_half = parts[0]
    bottom_half = parts[1]
    
    unposted_parts = bottom_half.split(archived_marker, 1)
    unposted_content = unposted_parts[0].strip()
    archived_content = unposted_parts[1].strip() if len(unposted_parts) > 1 else ""
    
    # Check if there is actual content beyond the placeholder text
    clean_unposted = re.sub(r'^\*\(.*?\)\*', '', unposted_content, flags=re.MULTILINE).strip()
    
    # Extract last archived entry as fallback
    last_archived = None
    if archived_content:
        # Most recent archived is usually at the top
        archived_entries = re.split(r'(?m)^##\s+\[', archived_content)
        if len(archived_entries) > 1:
            last_archived = "## [" + archived_entries[1].split("---")[0].strip()
        else:
            last_archived = archived_content.split("---")[0].strip()

    if not clean_unposted:
        return None, last_archived
        
    # Build the new file content: move the unposted stuff down to archive
    new_content = (
        top_half + 
        unposted_marker + "\n*(New entries will be automatically appended here by the Git Hook)*\n\n\n" +
        archived_marker + "\n" +
        clean_unposted + "\n\n---\n\n" +
        archived_content
    )
    
    with open(BUILD_LOG_PATH, "w", encoding="utf-8") as f:
        f.write(new_content)
        
    return clean_unposted, last_archived


def run_bip_batch_cycle():
    """
    Called 3-4 times a day by the main scheduler loop.
    Reads batched logs, asks LLM to write a massive post, and saves to DB.
    """
    logger.info("Running BIP Batch Cycle...")
    
    raw_progress, last_archived = extract_and_archive_unposted_progress()
    
    post_type = "new_progress"
    details_to_use = raw_progress

    if not raw_progress:
        logger.info("No unposted progress found. Checking for archived fallback...")
        if last_archived and last_archived.strip() and last_archived.strip() != "*(Logs that have already been posted are moved here)*":
            logger.info("Using last archived progress for a reflection post.")
            post_type = "reflection"
            details_to_use = last_archived
        else:
            logger.info("No unposted or archived progress found. Skipping cycle.")
            return
        
    # We have progress! Let's build a fake "latest_entry" payload for the LLM
    log_entry = {
        "title": "Batched Engineering Sprint" if post_type == "new_progress" else "Reflection on Last Build",
        "tags": ["#BuildInPublic", "#Engineering", "#Shipping"],
        "details": details_to_use,
        "images": [] # For fully automated, we skip images or parse them from the log if they existed
    }
    
    db: Session = SessionLocal()
    try:
        persona_path = os.getenv("PERSONA_DIR", "./data/personas/ahmad") + "/persona.md"
        persona_text = ""
        if os.path.exists(persona_path):
            with open(persona_path, "r", encoding="utf-8") as f:
                persona_text = f.read()

        logger.info(f"Sending {post_type} progress to LLM for LinkedIn...")
        generated_content = generate_build_in_public_post(log_entry, persona_text, post_type=post_type)
        
        new_post = Post(
            account="linkedin",
            status="draft", 
            hook_type="Technical Storytelling",
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
                x_json = generate_x_bip_post(log_entry, x_prompt_text)
                if x_json.get("is_thread") and x_json.get("thread_posts"):
                    x_content = "\n\n---\n\n".join(x_json["thread_posts"])
                else:
                    x_content = x_json.get("post", "")
                
                if x_content:
                    db.add(Post(
                        account="twitter",
                        status="draft",
                        hook_type=x_json.get("type", "build_update"),
                        topic_pillar="BIP: Batched Sprint",
                        content_text=f"{x_content}\n\n[NOTE: {x_json.get('note', '')}]",
                        format="thread" if x_json.get("is_thread") else "text",
                        source="bip_scheduler"
                    ))
            except Exception as e:
                logger.error(f"Failed to generate X post: {e}")

        # Reddit Post
        if reddit_prompt_text:
            logger.info("Sending batched progress to LLM for Reddit...")
            try:
                from services.llm import generate_reddit_bip_post
                reddit_json = generate_reddit_bip_post(log_entry, reddit_prompt_text)
                reddit_content = f"# {reddit_json.get('title', 'Build Update')}\n\n{reddit_json.get('body', '')}\n\n**Ask**: {reddit_json.get('genuine_ask', '')}"
                
                db.add(Post(
                    account="reddit",
                    status="draft",
                    hook_type=f"r/{reddit_json.get('subreddit', 'entrepreneur')}",
                    topic_pillar="BIP: Batched Sprint",
                    content_text=f"{reddit_content}\n\n[NOTE: {reddit_json.get('note', '')}]",
                    format="text",
                    source="bip_scheduler"
                ))
            except Exception as e:
                logger.error(f"Failed to generate Reddit post: {e}")

        db.add(AuditLog(action="BIP Scheduler", details={
            "status": "success",
            "step": "bip_batch_generation",
            "reason": f"Generated drafts for {post_type} across LinkedIn, X, and Reddit",
        }))
        db.commit()
        logger.info("✅ Successfully generated BIP Post Drafts!")
        
        # Fully autonomous publishing
        from api_routes.mirofish import run_debate_simulation
        from publishers.linkedin import publish_to_linkedin
        import asyncio
        
        logger.info("Running MiroFish simulation on generated BIP post...")
        confidence, passed = run_debate_simulation(db, str(new_post.id), generated_content)
        
        new_post.mirofish_confidence = confidence
        new_post.mirofish_gate_result = "pass" if passed else "fail"
        db.commit()
        
        if passed:
            logger.info("Post passed MiroFish! Publishing to LinkedIn...")
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
            except Exception as e:
                new_post.status = "failed"
                logger.error(f"Exception publishing to LinkedIn: {e}")
            db.commit()
        else:
            logger.warning("BIP Post failed MiroFish gate. Left as draft.")
        
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

"""
Oybit — Comment Opportunities Module (GAP 2.4 / GAP 7.6)
Detects high-leverage posts from target creators on LinkedIn and Reddit,
and drafts intelligent, non-spammy comments in Ahmad's voice to drive profile visits.
"""
import logging
from backend.content.generator import call_openrouter_raw

logger = logging.getLogger(__name__)

def find_linkedin_opportunities(target_creators: list) -> list:
    """
    Simulates finding recent posts from target creators.
    In production, this would call LinkedIn API or a scraping service like Phantombuster.
    """
    logger.info("Scanning for LinkedIn comment opportunities... (GAP 2.4)")
    # Stub returning a simulated opportunity
    return [{"platform": "linkedin", "author": "target_creator", "content": "Just shipped a new vector DB feature!"}]

def find_reddit_opportunities(subreddits: list) -> list:
    """
    Simulates finding top rising posts on Reddit (GAP 7.6).
    """
    logger.info("Scanning for Reddit comment opportunities... (GAP 7.6)")
    # Stub returning a simulated opportunity
    return [{"platform": "reddit", "subreddit": "r/SaaS", "content": "How do you handle background workers in FastAPI?"}]

def draft_comment(post_content: str, persona_path: str) -> str:
    """
    Drafts an intelligent comment adding technical or strategic value.
    Never uses "Great post!" or generic filler.
    """
    prompt = f"""
    Draft a comment for this post: "{post_content}"
    Rules:
    - Add real technical or strategic insight.
    - No generic praise.
    - Use Ahmad's direct, technical tone.
    - Max 2 sentences.
    """
    try:
        return call_openrouter_raw(prompt=prompt, system_prompt="You are a senior tech founder leaving a high-value comment.")
    except Exception as e:
        logger.error(f"Failed to draft comment: {e}")
        return ""

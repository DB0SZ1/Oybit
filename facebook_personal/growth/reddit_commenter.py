"""
Oybit — Reddit Commenter (Draft Generator)
Calls OpenRouter to draft a comment in Ahmad's voice for a specific Reddit thread.
Does NOT auto-post (requires manual approval).
(GAPS_FINAL 9.2)
"""
import os
import json
from content.generator import call_openrouter
from logger import get_logger

logger = get_logger("reddit_commenter")

def draft_reddit_comment(thread_topic: str, thread_context: str, persona_path: str = None) -> str:
    """
    Drafts a value-add comment in Ahmad's persona.
    """
    try:
        persona_content = "Focus on technical architecture, pragmatic advice, and real consequences."
        if persona_path and os.path.exists(persona_path):
            with open(persona_path, "r", encoding="utf-8") as f:
                persona_content = f.read()
                
        system_prompt = f"""You are drafting a Reddit comment on behalf of Ahmad Idris Rabiu.
        Your goal is to provide a highly valuable, concise, pragmatic answer.
        Do not sound like a marketing bot. Be direct, a little blunt, and highly technical if relevant.
        
        Persona Context:
        {persona_content[:1500]}
        
        Rules:
        1. No pleasantries (don't start with "Great question!" or "I'd suggest...")
        2. Get straight to the system insight or consequence.
        3. Aim for 2-4 short paragraphs.
        """
        
        user_prompt = f"Reddit Thread Title: {thread_topic}\n\nContext:\n{thread_context}\n\nDraft the comment:"
        
        # We assume call_openrouter returns a list of variants.
        variants = call_openrouter(system_prompt, user_prompt, model=os.getenv("OPENROUTER_DEEP_MODEL"))
        
        if variants and len(variants) > 0:
            return variants[0]
        return ""
    except Exception as e:
        logger.error(f"Failed to draft reddit comment: {e}")
        return ""

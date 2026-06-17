import os
import requests
import json
import logging
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("llm_service")

def generate_post_content(persona_text: str, topic: str, post_length: str = "long") -> str:
    """
    Generates a dynamic post using OpenRouter, conditioned on the persona and the selected topic/trend.
    """
    api_key = os.getenv("OPENROUTER_API_KEY")
    model = os.getenv("OPENROUTER_DEFAULT_MODEL", "google/gemini-2.5-flash")
    
    if not api_key:
        logger.error("OPENROUTER_API_KEY is not set.")
        # Fallback to mock content if no API key is present
        return "I gave an AI agent access to my LinkedIn for 30 days. Here's what happened to my engagement: [Thread]"
        
    system_prompt = f"""You are writing a LinkedIn post for a real person. 
Here are their exact Persona Rules and Identity:
{persona_text}

CRITICAL RULES:
1. Write EXACTLY ONE post. No metadata, no introduction, no hashtags, no "Here is your post:".
2. You MUST strictly adhere to the "Voice & Tone" and "Hard Stops" from the persona.
3. The post MUST feel human, alive, opinionated, and authentic.
"""

    if post_length == "short":
        system_prompt += "\n4. Write a SHORT-FORM, punchy post. Extremely direct. Under 50 words. No fluff."
    else:
        system_prompt += "\n4. LinkedIn requires LONG-FORM content. Write a detailed, multi-paragraph story (at least 150-250 words).\n5. Use plenty of whitespace between paragraphs."

    user_prompt = f"Write a new LinkedIn post focused on the following topic or trend: {topic}"
    
    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "HTTP-Referer": "https://oybit.nyvora.com",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "max_tokens": 800,
                "temperature": 0.8
            },
            timeout=30
        )
        
        
        response.raise_for_status()
        data = response.json()
        
        content = data["choices"][0]["message"]["content"].strip()
        return content
    except Exception as e:
        error_msg = str(e)
        if 'response' in locals() and hasattr(response, 'text'):
            error_msg += f" | Body: {response.text}"
        logger.error(f"Failed to generate LLM content: {error_msg}")
        # Fallback content if LLM fails
        return f"Just spent 4 hours fighting with {topic} and the results were unexpected. Here's what I learned building this in public... 🧵"


def generate_build_in_public_post(log_entry: dict, persona_text: str, post_type: str = "new_progress") -> str:
    """
    Generates a deeply contextual Build-in-Public post.
    post_type can be "new_progress" or "reflection".
    """
    api_key = os.getenv("OPENROUTER_API_KEY")
    model = os.getenv("OPENROUTER_DEFAULT_MODEL", "google/gemini-2.5-flash")
    
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY is not set.")

    if post_type == "new_progress":
        system_focus = "3. You MUST seamlessly integrate the technical details and struggle provided in the user prompt.\n4. Translate the raw technical details into an engaging story about WHY this matters, the problem it solves, and what you learned."
        user_focus = "Write my LinkedIn post about this progress update."
    else:
        system_focus = "3. You MUST reflect deeply on the technical details provided, which represents your LAST completed feature.\n4. Write a high-value, 'learnable' post sharing a major lesson, an architectural decision, or a deep dive into why this feature is a game-changer, even if you didn't write new code today."
        user_focus = "Write a reflective, high-value educational LinkedIn post about this feature and what I learned."

    system_prompt = f"""You are a startup founder and engineer building your product in public on LinkedIn.
Here is your Persona document that dictates your exact Voice, Tone, and Hard Stops:

{persona_text}

CRITICAL RULES:
1. Write EXACTLY ONE post. No metadata, no introduction, no "Here is your post:".
2. Write a LONG-FORM, story-driven post (at least 200 words). Use whitespace.
{system_focus}
5. If there are tags provided, weave the concepts of those tags into the narrative naturally. Do NOT just dump hashtags at the end.
"""

    user_prompt = f"""Here is my latest Build Log entry for this feature:
Title: {log_entry['title']}
Tags: {', '.join(log_entry['tags'])}
Details:
{log_entry['details']}

{user_focus}"""

    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "HTTP-Referer": "https://oybit.nyvora.com",
            "Content-Type": "application/json",
        },
        json={
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "max_tokens": 1500,
            "temperature": 0.6
        },
        timeout=30
    )
    
    response.raise_for_status()
    data = response.json()
    return data["choices"][0]["message"]["content"].strip()

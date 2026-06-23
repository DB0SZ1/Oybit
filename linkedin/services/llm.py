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
        from llm.generator import call_openrouter_raw
        content = call_openrouter_raw(
            system_prompt=system_prompt,
            prompt=user_prompt,
            model=model,
            temperature=0.8,
            max_tokens=800
        )
        return content
    except Exception as e:
        logger.error(f"Failed to generate LLM content: {e}")
        # Fallback content if LLM fails
        return f"Just spent 4 hours fighting with {topic} and the results were unexpected. Here's what I learned building this in public... 🧵"


def generate_build_in_public_post(log_entry: dict, persona_text: str, day_number: int, post_type: str) -> str:
    """
    Generates a deeply contextual Build-in-Public post for LinkedIn using the new strategy.
    """
    api_key = os.getenv("OPENROUTER_API_KEY")
    model = os.getenv("OPENROUTER_DEFAULT_MODEL", "google/gemini-2.5-flash")
    
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY is not set.")

    prompt_path = os.path.join(os.getcwd(), "persona_data", "linkedin_bip_prompt.txt")
    system_prompt = ""
    if os.path.exists(prompt_path):
        with open(prompt_path, "r", encoding="utf-8") as f:
            system_prompt = f.read()

    user_prompt = f"""Here is my latest Build Log entry for this feature:
Title: {log_entry['title']}
Tags: {', '.join(log_entry['tags'])}
Details:
{log_entry['details']}

INSTRUCTIONS:
Today is Day {day_number} of 30.
You must write a "{post_type}" post exactly following the formula defined in the system prompt for this specific type.
DO NOT output any metadata, JSON, or "Here is your post". Just the raw post text ready to be published on LinkedIn."""

    from llm.generator import call_openrouter_raw
    return call_openrouter_raw(
        system_prompt=system_prompt,
        prompt=user_prompt,
        model=model,
        temperature=0.6,
        max_tokens=1500
    ).strip()


def generate_x_bip_post(log_entry: dict, prompt_text: str, day_number: int, post_type: str) -> dict:
    """
    Generates an X (Twitter) Build-in-Public post using the detailed system prompt.
    Returns a JSON dict.
    """
    api_key = os.getenv("OPENROUTER_API_KEY")
    model = os.getenv("OPENROUTER_DEFAULT_MODEL", "google/gemini-2.5-flash")
    
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY is not set.")

    user_prompt = f"""Here is my latest Build Log entry for this commit:
Title: {log_entry['title']}
Tags: {', '.join(log_entry['tags'])}
Details:
{log_entry['details']}

INSTRUCTIONS:
Today is Day {day_number} of 30.
You must write a "{post_type}" post exactly following the formula defined in the system prompt for this specific type.
Follow the system prompt precisely and generate the JSON payload for X."""

    from llm.generator import call_openrouter_raw
    result_text = call_openrouter_raw(
        system_prompt=prompt_text,
        prompt=user_prompt,
        model=model,
        temperature=0.7,
        max_tokens=1500,
        response_format={"type": "json_object"}
    ).strip()
    if result_text.startswith("```json"):
        result_text = result_text[7:-3]
    elif result_text.startswith("```"):
        result_text = result_text[3:-3]
        
    return json.loads(result_text.strip())


def generate_reddit_bip_post(log_entry: dict, prompt_text: str, day_number: int, post_type: str) -> dict:
    """
    Generates a Reddit Build-in-Public post using the detailed system prompt.
    Returns a JSON dict.
    """
    api_key = os.getenv("OPENROUTER_API_KEY")
    model = os.getenv("OPENROUTER_DEFAULT_MODEL", "google/gemini-2.5-flash")
    
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY is not set.")

    user_prompt = f"""Here is my latest Build Log entry for this commit:
Title: {log_entry['title']}
Tags: {', '.join(log_entry['tags'])}
Details:
{log_entry['details']}

INSTRUCTIONS:
Today is Day {day_number} of 30.
You must write a "{post_type}" post exactly following the formula defined in the system prompt for this specific type.
Follow the system prompt precisely and generate the JSON payload for Reddit."""

    from llm.generator import call_openrouter_raw
    result_text = call_openrouter_raw(
        system_prompt=prompt_text,
        prompt=user_prompt,
        model=model,
        temperature=0.7,
        max_tokens=2000,
        response_format={"type": "json_object"}
    ).strip()
    if result_text.startswith("```json"):
        result_text = result_text[7:-3]
    elif result_text.startswith("```"):
        result_text = result_text[3:-3]
        
    return json.loads(result_text.strip())

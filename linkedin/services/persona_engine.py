import os
import json
import logging
import requests
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("persona_engine")

def _call_openrouter(system_prompt: str, user_prompt: str) -> str:
    """Helper to call OpenRouter for persona generation."""
    api_key = os.getenv("OPENROUTER_API_KEY")
    model = os.getenv("OPENROUTER_DEFAULT_MODEL", "meta-llama/llama-3.3-70b-instruct:free")
    
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY is not set.")
        
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
            "temperature": 0.5
        },
        timeout=60
    )
    
    try:
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"].strip()
    except Exception as e:
        error_msg = str(e)
        if hasattr(response, 'text'):
            error_msg += f" | Body: {response.text}"
        logger.error(f"Persona Engine LLM failed: {error_msg}")
        raise

def generate_initial_persona(answers_dict: dict) -> str:
    """
    Synthesizes the raw 60-question onboarding answers into a cohesive persona.md file.
    """
    system_prompt = """You are an expert personal brand architect and digital ghostwriter.
Your task is to take raw onboarding answers from a client and synthesize them into a highly structured, comprehensive "Persona Document".
This document will be used by an AI to ghostwrite their LinkedIn posts.

The document should be formatted in Markdown and include:
1. Core Identity & Authority (Who they are, what they do)
2. Voice & Tone (How they sound, adjectives, humor style, formatting preferences)
3. Content Pillars & Angles (What they talk about, their hot takes)
4. Target Audience (Who they are writing for and what those people want)
5. Core Narratives & Stories (Their background, hard moments, transformation)
6. Hard Stops & Anti-Patterns (What they NEVER do, say, or sound like)

Ensure the output is clean, readable, and directly actionable for an AI writing agent.
"""
    
    user_prompt = f"Here are the raw onboarding answers provided by the user:\n\n{json.dumps(answers_dict, indent=2)}\n\nPlease synthesize this into the final Persona Document in Markdown."
    
    return _call_openrouter(system_prompt, user_prompt)


def relearn_from_analytics(current_persona: str, analytics_data: dict) -> str:
    """
    Takes the current persona and recent performance data, and asks the LLM to rewrite the persona to incorporate new lessons learned.
    """
    system_prompt = """You are an elite LinkedIn growth strategist and AI persona architect.
You are managing an AI ghostwriter's Persona Document. The AI uses this document to generate posts.

Your task is to:
1. Review the Current Persona.
2. Review the Recent Analytics & Feedback Loop (what worked, what failed, what the audience loved).
3. Output an UPDATED version of the Persona Document. 
   - Integrate the new "Lessons Learned".
   - Adjust the Voice & Tone or Content Pillars if the analytics suggest a pivot.
   - Add a new section at the very top called "Active Feedback Loop & Optimization" detailing the latest strategic pivots.

Output ONLY the updated Markdown document.
"""
    
    user_prompt = f"""### Current Persona:
{current_persona}

### Recent Analytics & Feedback:
{json.dumps(analytics_data, indent=2)}

Please generate the newly optimized and updated Persona Document.
"""
    
    return _call_openrouter(system_prompt, user_prompt)

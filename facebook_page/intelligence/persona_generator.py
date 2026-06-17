"""
Persona Generator — Agent A Module

Takes answers from the Onboarding Session and intelligently merges them
into the existing persona.md file using an LLM.
"""

import os
import json
import logging
from config import PERSONA_DIR

try:
    import httpx
    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False

logger = logging.getLogger(__name__)


def update_persona_with_answers(answers: dict) -> bool:
    """
    Intelligently merge the onboarding answers into the existing persona.md.
    """
    from onboarding.questions import get_all_questions

    api_key = os.getenv("OPENROUTER_API_KEY", "")
    if not api_key or not HAS_HTTPX:
        logger.error("Cannot update persona: OPENROUTER_API_KEY not set or httpx missing.")
        return False

    # 1. Load existing persona
    persona_path = os.path.join(PERSONA_DIR, "persona.md")
    existing_persona = ""
    if os.path.exists(persona_path):
        with open(persona_path, "r", encoding="utf-8") as f:
            existing_persona = f.read()

    # 2. Format answers with their questions
    all_questions = {q["id"]: q["question_text"] for q in get_all_questions()}
    
    formatted_answers = []
    for q_id, answer in answers.items():
        if not answer:
            continue
        q_text = all_questions.get(q_id, "Unknown Question")
        formatted_answers.append(f"Q: {q_text}\nA: {answer}")

    if not formatted_answers:
        logger.warning("No answers provided to update persona.")
        return True

    answers_text = "\n\n".join(formatted_answers)

    # 3. Construct prompt
    prompt = f"""You are an expert Brand Strategist and AI Persona Architect.
I have an existing AI Persona document (markdown format) that dictates how an autonomous agent posts on social media.
The user just completed an onboarding questionnaire to refine this persona.

Your task is to INTELLIGENTLY MERGE the new answers into the existing persona document.
- DO NOT delete the core structure of the document.
- DO NOT just append the Q&A to the bottom.
- DO integrate the insights (tone, constraints, topics, rules, strategies) directly into the relevant sections (Identity, Voice & Tone, Content Pillars, Hard Stops, etc.).
- IF the user's answers contradict the existing persona, the new answers take precedence (update the persona accordingly).

=== EXISTING PERSONA.MD ===
{existing_persona}

=== NEW ONBOARDING ANSWERS ===
{answers_text}

Output the completely updated markdown document. Do not output anything else. Do not wrap it in a markdown block (no ```markdown). Just raw markdown text.
"""

    try:
        model = os.getenv("OPENROUTER_DEFAULT_MODEL", "meta-llama/llama-4-scout:free")
        response = httpx.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "HTTP-Referer": "https://oybit.nyvora.com",
                "X-Title": "Oybit",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": "You are an AI Persona Architect. Output only the updated raw markdown persona."},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.2,
            },
            timeout=120.0,
        )
        response.raise_for_status()
        
        updated_persona = response.json()["choices"][0]["message"]["content"].strip()
        
        # Clean up if the LLM still decided to wrap it in markdown block
        import re
        updated_persona = re.sub(r'^```(?:markdown)?\s*', '', updated_persona)
        updated_persona = re.sub(r'\s*```$', '', updated_persona)

        # 4. Save back to file
        with open(persona_path, "w", encoding="utf-8") as f:
            f.write(updated_persona)
            
        logger.info("Successfully updated persona.md with onboarding answers.")
        return True

    except Exception as e:
        logger.error(f"Failed to update persona via LLM: {e}")
        return False

"""
Content Generator (Prompt Assembly) — Agent A Module
Agent A owns the prompt assembly logic. Agent B will write the OpenRouter call wrapper.
"""

from persona_engine.prompt_builder import assemble_generation_prompt as _assemble

def assemble_generation_prompt(
    persona_path: str,
    simulation_log_path: str,
    topic_brief: str,
    platform: str,
    format_type: str = "text",
    account: str = None,
) -> dict:
    """
    Assemble the full system + user prompt.
    Delegates to the implementation in persona_engine/prompt_builder.py
    Returns: dict with 'system_prompt' and 'user_prompt' keys.
    """
    return _assemble(
        persona_path=persona_path,
        simulation_log_path=simulation_log_path,
        topic_brief=topic_brief,
        platform=platform,
        format_type=format_type,
        account=account
    )

import httpx
import logging
import os
import re

logger = logging.getLogger(__name__)

def _parse_variants(content: str) -> dict:
    """Parse <variant account="xxx"> blocks from OpenRouter output."""
    variants = {}
    pattern = re.compile(r'<variant\s+account=[\'"]([^\'"]+)[\'"]>(.*?)</variant>', re.DOTALL)
    matches = pattern.findall(content)
    
    if matches:
        for account, txt in matches:
            variants[account] = txt.strip()
    else:
        # Fallback if no tags generated
        txt = content.strip()
        variants = {
            "instagram_personal": txt,
            "instagram_brand": txt,
            "facebook": txt,
            "linkedin": txt
        }
    return variants

def generate_content(prompt_dict: dict, dry_run: bool = False, http_client=None) -> dict:
    """
    Call OpenRouter with the assembled prompt.
    Returns: dict of account -> content
    """
    api_key = os.getenv("OPENROUTER_API_KEY", "")
    if not api_key:
        raise ValueError("Missing OPENROUTER_API_KEY")

    client = http_client or httpx.Client(timeout=60)
    
    sys_p = prompt_dict.get("system_prompt", "")
    usr_p = prompt_dict.get("user_prompt", "")

    payload = {
        "model": os.getenv("OPENROUTER_DEFAULT_MODEL", "meta-llama/llama-4-scout"),
        "messages": [
            {"role": "system", "content": sys_p},
            {"role": "user", "content": usr_p}
        ],
        "temperature": 0.7
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "HTTP-Referer": "https://oybit.nyvora.com",
        "X-Title": "Oybit"
    }

    models_to_try = [
        os.getenv("OPENROUTER_DEFAULT_MODEL", "google/gemini-2.0-flash-lite-preview-02-05:free"),
        "qwen/qwen-2.5-72b-instruct:free",
        "meta-llama/llama-3.3-70b-instruct:free",
        "mistralai/mistral-7b-instruct:free",
        "google/gemma-2-9b-it:free"
    ]

    import time
    try:
        for attempt in range(3):
            for current_model in models_to_try:
                payload["model"] = current_model
                try:
                    resp = client.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload)
                    if resp.status_code == 200:
                        data = resp.json()
                        if "error" in data:
                            logger.error(f"OpenRouter returned error for {current_model}: {data['error']}")
                            continue # Try next model
                        try:
                            raw_text = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                        except (IndexError, AttributeError):
                            raw_text = ""
                        return _parse_variants(raw_text)
                    elif resp.status_code in (400, 404, 429) or resp.status_code >= 500:
                        logger.warning(f"Model {current_model} failed with {resp.status_code}, falling back to next model...")
                        continue
                    else:
                        resp.raise_for_status()
                except Exception as e:
                    logger.warning(f"Network or request error for {current_model}: {e}")
                    continue
            
            if attempt < 2:
                logger.warning(f"Attempt {attempt+1} failed for all models. Sleeping for 15s before retrying...")
                time.sleep(15)
                
        raise Exception("OpenRouter: All fallback models failed or were rate-limited.")
    except Exception as e:
        logger.error(f"OpenRouter API call failed: {e}")
        raise


def call_openrouter_raw(
    prompt: str,
    system_prompt: str = "You are a helpful assistant. Return only the requested format.",
    max_tokens: int = 500,
    model: str = None,
    temperature: float = 0.7,
) -> str:
    """
    Low-level OpenRouter call that returns raw text response.
    Used by MiroFish agents, simulation, and other modules that need
    direct AI access without the content generation pipeline.

    Args:
        prompt: user prompt text
        system_prompt: system prompt text
        max_tokens: maximum tokens in response
        model: override model (defaults to OPENROUTER_DEFAULT_MODEL)
        temperature: sampling temperature

    Returns:
        Raw text from the AI response

    Raises:
        ValueError: if OPENROUTER_API_KEY is missing
        Exception: on API failure after retries
    """
    api_key = os.getenv("OPENROUTER_API_KEY", "")
    if not api_key:
        raise ValueError("Missing OPENROUTER_API_KEY")

    models_to_try = [model] if model else [
        os.getenv("OPENROUTER_DEFAULT_MODEL", "google/gemini-2.0-flash-lite-preview-02-05:free"),
        "qwen/qwen-2.5-72b-instruct:free",
        "meta-llama/llama-3.3-70b-instruct:free",
        "mistralai/mistral-7b-instruct:free",
        "google/gemma-2-9b-it:free"
    ]

    payload = {
        "model": models_to_try[0],
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "HTTP-Referer": "https://oybit.nyvora.com",
        "X-Title": "Oybit",
    }

    import time
    with httpx.Client(timeout=60) as client:
        for attempt in range(3):
            for current_model in models_to_try:
                payload["model"] = current_model
                try:
                    resp = client.post(
                        "https://openrouter.ai/api/v1/chat/completions",
                        headers=headers,
                        json=payload,
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        error_payload = data.get("error")
                        provider_code = data.get("code")
                        if error_payload or (isinstance(provider_code, int) and provider_code >= 500):
                            logger.warning(
                                f"OpenRouter provider error for {current_model}: "
                                f"code={provider_code}, error={error_payload}"
                            )
                            continue # Try next model
                        try:
                            return data.get("choices", [{}])[0].get("message", {}).get("content", "")
                        except (IndexError, AttributeError):
                            return ""
                    elif resp.status_code == 429:
                        logger.warning(f"Model {current_model} rate-limited (429).")
                        continue
                    elif resp.status_code >= 500 or resp.status_code in (400, 404):
                        logger.warning(f"Model {current_model} failed with {resp.status_code}, falling back...")
                        continue
                    else:
                        resp.raise_for_status()
                except httpx.RequestError as e:
                    logger.warning(f"Network error trying {current_model}: {e}")
                    continue
                    
            if attempt < 2:
                logger.warning(f"Attempt {attempt+1} failed for all fallback models. Sleeping for 15s before retrying...")
                time.sleep(15)

    raise Exception("OpenRouter: All models and retries failed due to rate limits or errors.")


def call_openrouter(system_prompt: str, user_prompt: str, **kwargs) -> dict:
    """
    Wrapper around call_openrouter_raw for agent_b_routes compatibility.
    Returns parsed variants dict.
    """
    raw = call_openrouter_raw(
        prompt=user_prompt,
        system_prompt=system_prompt,
        **kwargs,
    )
    return _parse_variants(raw)


def repurposer(content: str) -> dict:
    """
    Take a single piece of content and create platform-specific variants.
    Returns dict of platform -> adapted content.
    """
    # For now, create simple variants with platform-specific formatting
    return {
        "linkedin": content,
        "instagram_personal": content[:2200] if len(content) > 2200 else content,
        "instagram_brand": content[:2200] if len(content) > 2200 else content,
        "facebook": content,
    }


def bulk_generate(briefs: list) -> list:
    """
    Generate content for multiple briefs in batch.
    Returns list of generation results.
    """
    results = []
    for brief in briefs:
        try:
            raw = call_openrouter_raw(prompt=brief)
            results.append({"brief": brief, "variants": _parse_variants(raw), "status": "ok"})
        except Exception as e:
            results.append({"brief": brief, "variants": {}, "status": "error", "error": str(e)})
    return results


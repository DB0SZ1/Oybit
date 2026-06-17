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

    try:
        max_retries = 3
        for attempt in range(max_retries):
            resp = client.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload)
            if resp.status_code == 200:
                data = resp.json()
                if "error" in data:
                    logger.error(f"OpenRouter returned error payload: {data['error']}")
                    raise Exception(f"OpenRouter Error: {data['error']}")
                try:
                    raw_text = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                except (IndexError, AttributeError):
                    raw_text = ""
                return _parse_variants(raw_text)
            elif resp.status_code == 429:
                import time
                retry_after = int(resp.headers.get("retry-after", 30))
                logger.warning({"event": "openrouter_rate_limit", "retry_after": retry_after, "attempt": attempt})
                if attempt < max_retries - 1:
                    time.sleep(retry_after)
                continue
            elif resp.status_code == 503:
                logger.error({"event": "openrouter_down", "attempt": attempt})
                # Fallback logic would go here if provided
                raise httpx.HTTPStatusError(f"HTTP 503: {resp.text[:200]}", request=resp.request, response=resp)
            else:
                resp.raise_for_status()
                
        raise Exception("OpenRouterRateLimitError: Max retries exceeded")
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

    if model is None:
        model = os.getenv("OPENROUTER_DEFAULT_MODEL", "meta-llama/llama-4-scout:free")

    payload = {
        "model": model,
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

    with httpx.Client(timeout=60) as client:
        for attempt in range(3):
            resp = client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=payload,
            )
            if resp.status_code == 200:
                data = resp.json()
                # Check for provider error payloads (HTTP 200 but body says 502/503)
                error_payload = data.get("error")
                provider_code = data.get("code")
                if error_payload or (isinstance(provider_code, int) and provider_code >= 500):
                    logger.warning(
                        f"OpenRouter provider error (attempt {attempt+1}/3): "
                        f"code={provider_code}, error={error_payload}"
                    )
                    if attempt < 2:
                        import time
                        backoff = 2 ** (attempt + 1)  # 2s, 4s, 8s
                        time.sleep(backoff)
                        continue
                    raise Exception(f"OpenRouter provider error after 3 retries: {data}")
                try:
                    return data.get("choices", [{}])[0].get("message", {}).get("content", "")
                except (IndexError, AttributeError):
                    return ""
            elif resp.status_code == 429:
                import time
                import random
                retry_after = int(resp.headers.get("retry-after", 30))
                jitter = random.randint(1, 5)
                logger.warning("OpenRouter rate limit", extra={"retry_after": retry_after, "jitter": jitter, "attempt": attempt})
                if attempt < 2:
                    time.sleep(retry_after + jitter)
                continue
            else:
                resp.raise_for_status()

    raise Exception("OpenRouter: max retries exceeded")


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


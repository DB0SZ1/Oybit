"""
Oybit — Image Generator (Pollinations.ai)
Free image generation — no API key needed.
Downloads image to local file and returns file path.
"""
import os
import logging
import time
from urllib.parse import quote

import httpx

logger = logging.getLogger(__name__)


def generate_image(prompt: str, width: int = 1080, height: int = 1080,
                   output_path: str = None, timeout: int = 120) -> str:
    """
    Generate an image via Pollinations.ai and save to local file.

    Args:
        prompt: text description for image generation
        width: image width in pixels
        height: image height in pixels
        output_path: where to save the image (auto-generated if None)
        timeout: request timeout in seconds

    Returns:
        local file path to the saved image
    """
    if not output_path:
        output_dir = os.getenv("RENDER_OUTPUT_DIR", "/tmp/oybit_renders")
        os.makedirs(output_dir, exist_ok=True)
        timestamp = int(time.time() * 1000)
        output_path = os.path.join(output_dir, f"img_{timestamp}.jpg")

    encoded_prompt = quote(prompt)
    url = f"https://image.pollinations.ai/prompt/{encoded_prompt}"
    params = {
        "width": width,
        "height": height,
        "nologo": "true",
        "enhance": "true",
        "model": "flux"
    }

    max_retries = 2
    for attempt in range(max_retries):
        try:
            client = httpx.Client(timeout=timeout, follow_redirects=True)
            response = client.get(url, params=params)
            response.raise_for_status()

            # Verify we got image data (not an error page)
            content_type = response.headers.get("content-type", "")
            if "image" not in content_type:
                raise ValueError(f"Pollinations returned non-image content: {content_type}")
            if len(response.content) < 1000:
                raise ValueError(f"Pollinations returned suspiciously small file: {len(response.content)} bytes")

            # Write to disk
            os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)
            with open(output_path, "wb") as f:
                f.write(response.content)

            logger.info(f"Image generated: {output_path} ({len(response.content)} bytes)")
            return output_path

        except Exception as e:
            logger.error(f"Image generation attempt {attempt+1} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(5)
            else:
                raise RuntimeError(f"Image generation failed after {max_retries} attempts: {e}")

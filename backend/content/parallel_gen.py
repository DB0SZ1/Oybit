"""
Oybit — Image + Text Simultaneous Generation (GAP 6.1)
Orchestrates parallel content + image generation for a single post.
"""
import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor

from backend.content.generator import generate_content
from backend.render_engine.image import generate_image

logger = logging.getLogger(__name__)

def generate_post_with_image(prompt_dict: dict, image_prompt: str,
                              dry_run: bool = False) -> dict:
    """
    Generate text content and image simultaneously.
    
    Returns:
        dict with 'variants' (text per account) and 'image_path'
    """
    with ThreadPoolExecutor(max_workers=2) as executor:
        text_future = executor.submit(generate_content, prompt_dict, dry_run)
        image_future = executor.submit(generate_image, image_prompt) if not dry_run else None
        
        variants = text_future.result()
        image_path = image_future.result() if image_future else "/tmp/dry_run_image.jpg"
    
    return {
        "variants": variants,
        "image_path": image_path
    }

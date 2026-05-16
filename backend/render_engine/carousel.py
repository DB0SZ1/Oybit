"""
Oybit — Carousel Renderer
Playwright + Jinja2 → 1080×1080 JPEG slides.
Async implementation for fast rendering.
"""
import os
import asyncio
import logging
import glob
import tempfile
from typing import Optional
from pathlib import Path
import img2pdf
from backend.utils.exceptions import CarouselRenderError

def verify_render_output(output_path: str, min_size_bytes: int = 10000):
    path_obj = Path(output_path)
    if not path_obj.exists():
        raise CarouselRenderError(f"Render output not found at {output_path}")
    if path_obj.stat().st_size < min_size_bytes:
        raise CarouselRenderError(f"Render output too small: {path_obj.stat().st_size} bytes")
    return True

from jinja2 import Environment, FileSystemLoader

logger = logging.getLogger(__name__)

TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "templates")


async def render_carousel(template_name: str, context: dict,
                          output_dir: str = None) -> list[str]:
    """
    Render carousel slides as 1080x1080 JPEG images.

    Args:
        template_name: HTML template file name (e.g. 'carousel_personal_ig.html')
        context: dict with slide_content[], brand_colors, fonts, account_type
        output_dir: directory to save output images

    Returns:
        list of file paths to rendered JPEG images
    """
    if output_dir is None:
        output_dir = os.getenv("RENDER_OUTPUT_DIR", "/tmp/oybit_renders")
    os.makedirs(output_dir, exist_ok=True)

    # Load template
    template_dir = os.getenv("CAROUSEL_TEMPLATE_DIR", TEMPLATE_DIR)
    if not os.path.exists(os.path.join(template_dir, template_name)):
        raise FileNotFoundError(
            f"Template '{template_name}' not found in {template_dir}. "
            f"Available templates: {os.listdir(template_dir) if os.path.exists(template_dir) else 'directory missing'}"
        )

    env = Environment(loader=FileSystemLoader(template_dir))
    template = env.get_template(template_name)

    slides = context.get("slide_content", [])
    if not slides:
        raise ValueError("No slide content provided in context")

    total_slides = len(slides)
    output_paths = []
    temp_html_files = []

    try:
        from playwright.async_api import async_playwright

        async with async_playwright() as p:
            executable_path = None
            
            # Windows Paths
            edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
            chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
            
            # Linux / Hosting Paths
            linux_chrome = "/usr/bin/google-chrome"
            linux_chromium = "/usr/bin/chromium-browser"
            linux_chromium_alt = "/usr/bin/chromium"

            if os.path.exists(edge_path):
                executable_path = edge_path
            elif os.path.exists(chrome_path):
                executable_path = chrome_path
            elif os.path.exists(linux_chrome):
                executable_path = linux_chrome
            elif os.path.exists(linux_chromium):
                executable_path = linux_chromium
            elif os.path.exists(linux_chromium_alt):
                executable_path = linux_chromium_alt
                
            browser_kwargs = {"headless": True}
            if executable_path:
                browser_kwargs["executable_path"] = executable_path
                
            browser = await p.chromium.launch(**browser_kwargs)

            for i, slide in enumerate(slides):
                slide_context = {
                    **context,
                    "slide_headline": slide.get("headline", ""),
                    "slide_body": slide.get("body", ""),
                    "lottie_url": slide.get("lottie_url", ""),
                    "slide_number": i + 1,
                    "total_slides": total_slides,
                    "brand_color_primary": context.get("brand_colors", {}).get("primary", "#1a1a2e"),
                    "brand_color_secondary": context.get("brand_colors", {}).get("secondary", "#16213e"),
                    "font_family": context.get("fonts", {}).get("family", "Inter, sans-serif"),
                    "logo_url": context.get("logo_url", ""),
                }

                html = template.render(**slide_context)

                # Write temp HTML
                temp_path = os.path.join(output_dir, f"temp_slide_{i}.html")
                with open(temp_path, "w", encoding="utf-8") as f:
                    f.write(html)
                temp_html_files.append(temp_path)

                # Screenshot
                page = await browser.new_page(viewport={"width": 1080, "height": 1080})
                await page.set_content(html, wait_until="networkidle")
                
                # Wait 1000ms for Lottie animations to fully initialize and draw the first frame
                if slide.get("lottie_url"):
                    await page.wait_for_timeout(1000)
                
                output_path = os.path.join(output_dir, f"slide_{i+1:02d}.jpg")
                await page.screenshot(
                    path=output_path,
                    type="jpeg",
                    quality=95,
                    clip={"x": 0, "y": 0, "width": 1080, "height": 1080}
                )
                await page.close()
                verify_render_output(output_path)
                output_paths.append(output_path)
                logger.info(f"Rendered slide {i+1}/{total_slides}: {output_path}")

            await browser.close()

    finally:
        # Clean up temp HTML files
        for temp_file in temp_html_files:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            except Exception:
                pass

    # Check if target is LinkedIn -> export as single PDF
    account = context.get("account", "")
    if account.startswith("linkedin") and output_paths:
        try:
            pdf_path = os.path.join(output_dir, "carousel.pdf")
            with open(pdf_path, "wb") as f:
                f.write(img2pdf.convert(output_paths))
            logger.info(f"Compiled {len(output_paths)} slides into PDF: {pdf_path}")
            
            # Clean up JPEGs since we only need the PDF for LinkedIn
            for p in output_paths:
                try:
                    os.remove(p)
                except Exception:
                    pass
                    
            return [pdf_path]
        except Exception as e:
            logger.error(f"Failed to compile PDF for LinkedIn: {e}. Falling back to JPEGs.")

    return output_paths


def render_carousel_sync(template_name: str, context: dict,
                         output_dir: str = None) -> list[str]:
    """Synchronous wrapper for render_carousel."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(
                    asyncio.run,
                    render_carousel(template_name, context, output_dir)
                )
                return future.result()
    except RuntimeError:
        pass
    return asyncio.run(render_carousel(template_name, context, output_dir))

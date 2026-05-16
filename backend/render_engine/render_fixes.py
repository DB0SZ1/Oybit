"""
Oybit — Rendering Fixes (GAPs 13.1–13.4)
Font loading, slide overflow, reel validation, and render queue.
"""
import asyncio
import logging
import os
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)

# ── GAP 13.1: Font Loading in Playwright ───────────────────────
GOOGLE_FONTS = ["Inter", "Outfit", "Playfair Display", "Space Grotesk"]

def get_font_css_import() -> str:
    """Generate CSS @import for Google Fonts to inject into carousel templates."""
    families = "|".join(f.replace(" ", "+") for f in GOOGLE_FONTS)
    return f'<link href="https://fonts.googleapis.com/css2?family={families}&display=swap" rel="stylesheet">'

def inject_fonts_into_html(html: str) -> str:
    """Inject Google Fonts link into HTML head."""
    font_link = get_font_css_import()
    if "<head>" in html:
        return html.replace("<head>", f"<head>\n{font_link}")
    return f"{font_link}\n{html}"


# ── GAP 13.2: Slide Overflow Validation ────────────────────────
def validate_slide_content(slides: list[dict], max_headline_chars: int = 60,
                            max_body_chars: int = 200) -> list[str]:
    """Check all slides for text overflow before rendering."""
    warnings = []
    for i, slide in enumerate(slides):
        headline = slide.get("headline", "")
        body = slide.get("body", "")
        
        if len(headline) > max_headline_chars:
            warnings.append(f"Slide {i+1}: headline ({len(headline)} chars) exceeds {max_headline_chars} char limit")
        if len(body) > max_body_chars:
            warnings.append(f"Slide {i+1}: body ({len(body)} chars) exceeds {max_body_chars} char limit")
    
    return warnings

def truncate_slide_text(text: str, max_chars: int) -> str:
    """Smart truncation that doesn't break words."""
    if len(text) <= max_chars:
        return text
    truncated = text[:max_chars-3].rsplit(' ', 1)[0]
    return truncated + "..."


# ── GAP 13.3: Instagram Reel Pre-Upload Validation ─────────────
def validate_reel(video_path: str) -> dict:
    """Validate video meets Instagram Reel requirements before upload."""
    from backend.utils.shell import run_command
    
    result = {"valid": True, "errors": [], "warnings": []}
    
    path = Path(video_path)
    if not path.exists():
        result["valid"] = False
        result["errors"].append("Video file not found")
        return result
    
    # Check file size (max 100MB for Reels)
    size_mb = path.stat().st_size / (1024 * 1024)
    if size_mb > 100:
        result["valid"] = False
        result["errors"].append(f"File too large: {size_mb:.1f}MB (max 100MB)")
    
    # Use ffprobe to check duration and resolution
    rc, stdout, stderr = run_command([
        "ffprobe", "-v", "quiet", "-print_format", "json",
        "-show_format", "-show_streams", str(video_path)
    ])
    
    if rc == 0:
        import json
        try:
            probe = json.loads(stdout)
            
            # Check duration (3-90 seconds for Reels)
            duration = float(probe.get("format", {}).get("duration", 0))
            if duration < 3:
                result["valid"] = False
                result["errors"].append(f"Too short: {duration:.1f}s (min 3s)")
            elif duration > 90:
                result["valid"] = False
                result["errors"].append(f"Too long: {duration:.1f}s (max 90s)")
            elif duration > 60:
                result["warnings"].append(f"Duration {duration:.1f}s — 15-30s recommended for best performance")
            
            # Check resolution
            for stream in probe.get("streams", []):
                if stream.get("codec_type") == "video":
                    width = stream.get("width", 0)
                    height = stream.get("height", 0)
                    if width < 500 or height < 500:
                        result["warnings"].append(f"Low resolution: {width}x{height}")
                    if height < width:
                        result["warnings"].append("Reels should be vertical (9:16)")
        except json.JSONDecodeError:
            result["warnings"].append("Could not parse ffprobe output")
    else:
        result["warnings"].append("ffprobe not available, skipping detailed validation")
    
    return result


# ── GAP 13.4: Render Queue (Max 1 Concurrent) ─────────────────
_render_semaphore = asyncio.Semaphore(1)

async def queued_render(render_fn, *args, **kwargs):
    """Wrap any render function with a concurrency limiter."""
    async with _render_semaphore:
        if asyncio.iscoroutinefunction(render_fn):
            return await render_fn(*args, **kwargs)
        else:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, lambda: render_fn(*args, **kwargs))

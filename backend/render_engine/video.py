"""
Oybit — Video Renderer
Remotion render + ffmpeg post-processing for platform compliance.
"""
import json
import os
import subprocess
import logging
from pathlib import Path
from backend.utils.shell import run_command
from backend.utils.exceptions import VideoRenderError

logger = logging.getLogger(__name__)

def verify_video_output(output_path: str):
    path_obj = Path(output_path)
    if not path_obj.exists():
        raise VideoRenderError(f"Video output not found at {output_path}")
    
    # Try ffprobe validation, but fallback if ffprobe missing
    rc, stdout, stderr = run_command(["ffprobe", "-v", "error", "-show_entries",
        "format=duration", "-of", "json", str(output_path)])
    if rc != 0:
        # Check if the error is just 'ffprobe not found' natively. We don't want to crash on dev machines missing it.
        if "ffprobe" in stderr or "No such file or directory" in stderr:
            logger.warning(f"ffprobe not found or failed, skipping hard validation: {stderr}")
        else:
            raise VideoRenderError(f"ffprobe validation failed: {stderr}")


def render_video(composition_id: str, props: dict, output_path: str,
                 remotion_dir: str = None) -> str:
    """
    Render a video using Remotion CLI.

    Args:
        composition_id: Remotion composition name (e.g. "PersonalBrand")
        props: dict with content, colors, timing, account_type
        output_path: path for output .mp4 file
        remotion_dir: directory containing Remotion project

    Returns:
        path to rendered .mp4 file
    """
    if remotion_dir is None:
        remotion_dir = os.getenv("REMOTION_PROJECT_DIR",
                                  os.path.join(os.path.dirname(__file__), "templates", "video"))

    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)

    props_json = json.dumps(props)

    cmd = [
        "npx", "remotion", "render",
        "src/index.tsx",
        composition_id,
        output_path,
        "--props", props_json,
        "--codec", "h264",
        "--image-format", "jpeg"
    ]

    logger.info(f"Rendering video: {composition_id} → {output_path}")

    result = subprocess.run(
        cmd, capture_output=True, text=True, cwd=remotion_dir,
        timeout=600  # 10 min timeout
    )

    if result.returncode != 0:
        raise RuntimeError(f"Remotion render failed: {result.stderr}")

    verify_video_output(output_path)

    logger.info(f"Video rendered: {output_path}")
    return output_path


def process_for_instagram_reel(input_path: str, output_path: str) -> str:
    """
    Post-process video for Instagram Reels (9:16, 1080x1920).
    """
    cmd = [
        "ffmpeg", "-y", "-i", input_path,
        "-vf", "scale=1080:1920,setsar=1",
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "23",
        "-movflags", "+faststart",
        "-c:a", "aac",
        "-b:a", "128k",
        output_path
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg processing failed: {result.stderr}")

    return output_path


def process_for_facebook(input_path: str, output_path: str) -> str:
    """
    Post-process video for Facebook (16:9, 1280x720).
    """
    cmd = [
        "ffmpeg", "-y", "-i", input_path,
        "-vf", "scale=1280:720,setsar=1",
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "23",
        "-movflags", "+faststart",
        "-c:a", "aac",
        "-b:a", "128k",
        output_path
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg processing failed: {result.stderr}")

    return output_path


def render_and_process(composition_id: str, props: dict, output_path: str,
                       platform: str = "instagram_reel", remotion_dir: str = None) -> str:
    """
    Full render pipeline: Remotion → ffmpeg → platform-ready video.
    """
    raw_output = output_path.replace(".mp4", "_raw.mp4")

    render_video(composition_id, props, raw_output, remotion_dir)

    if platform == "instagram_reel":
        result = process_for_instagram_reel(raw_output, output_path)
    elif platform == "facebook":
        result = process_for_facebook(raw_output, output_path)
    else:
        # No post-processing needed
        os.rename(raw_output, output_path)
        result = output_path

    # Cleanup raw file
    if os.path.exists(raw_output):
        os.remove(raw_output)

    return result

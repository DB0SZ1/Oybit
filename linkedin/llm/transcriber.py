"""
Content Transcriber — Converts vlog audio to text via OpenAI Whisper API
and generates content briefs from the transcription.

Pipeline: video file → ffmpeg audio extraction → Whisper API → transcript → content briefs
"""

import os
import json
import subprocess
import tempfile
from pathlib import Path
from llm.generator import call_openrouter_raw
from logger import get_logger

logger = get_logger("content.transcriber")


def extract_audio(video_path: str, output_format: str = "mp3") -> str:
    """
    Extract audio from video file using ffmpeg.

    Args:
        video_path: path to the video file
        output_format: audio format (mp3, wav, etc.)

    Returns:
        Path to the extracted audio file
    """
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found: {video_path}")

    audio_path = tempfile.mktemp(suffix=f".{output_format}")

    cmd = [
        "ffmpeg", "-i", video_path,
        "-vn",  # No video
        "-acodec", "libmp3lame" if output_format == "mp3" else "pcm_s16le",
        "-ar", "16000",  # 16kHz for Whisper
        "-ac", "1",  # Mono
        "-y",  # Overwrite
        audio_path,
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if result.returncode != 0:
            raise RuntimeError(f"ffmpeg failed: {result.stderr[:500]}")
        logger.info("Audio extracted", extra={"source": video_path, "output": audio_path})
        return audio_path
    except FileNotFoundError:
        raise RuntimeError("ffmpeg not found — install ffmpeg to use vlog transcription")


def transcribe_audio(audio_path: str) -> str:
    """
    Transcribe audio using OpenAI Whisper API.

    Args:
        audio_path: path to the audio file

    Returns:
        Transcription text
    """
    import httpx

    api_key = os.getenv("OPENROUTER_API_KEY", "")
    if not api_key:
        raise ValueError("Missing OPENROUTER_API_KEY for Whisper transcription")

    # Use OpenAI-compatible Whisper endpoint
    whisper_url = os.getenv("WHISPER_API_URL", "https://api.openai.com/v1/audio/transcriptions")
    whisper_key = os.getenv("OPENAI_API_KEY", api_key)

    with open(audio_path, "rb") as audio_file:
        with httpx.Client(timeout=120) as client:
            response = client.post(
                whisper_url,
                headers={"Authorization": f"Bearer {whisper_key}"},
                files={"file": ("audio.mp3", audio_file, "audio/mpeg")},
                data={"model": "whisper-1", "language": "en"},
            )
            response.raise_for_status()
            data = response.json()

    transcript = data.get("text", "")
    logger.info("Audio transcribed", extra={"length": len(transcript), "words": len(transcript.split())})
    return transcript


def generate_briefs_from_transcript(
    transcript: str,
    platforms: list = None,
    max_briefs: int = 5,
) -> list:
    """
    Generate content briefs from a vlog transcript.
    Each brief is a standalone content idea derived from the vlog.

    Args:
        transcript: the transcribed text
        platforms: list of target platforms
        max_briefs: maximum number of briefs to generate

    Returns:
        list of content brief dicts
    """
    if platforms is None:
        platforms = ["linkedin", "instagram_personal"]

    prompt = (
        f"Analyze this vlog transcript and extract {max_briefs} distinct content ideas:\n\n"
        f'"""\n{transcript[:2000]}\n"""\n\n'
        f"Target platforms: {', '.join(platforms)}\n"
        f"For each idea, generate a brief with: topic, hook, key_points, platform, format.\n\n"
        f"Return ONLY valid JSON:\n"
        f'{{"briefs": [\n'
        f'  {{"topic": "...", "hook": "...", "key_points": ["..."], '
        f'"platform": "linkedin", "format": "text|carousel|poll"}}\n'
        f"]}}"
    )

    try:
        result = call_openrouter_raw(prompt, max_tokens=600)
        cleaned = result.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[1]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]

        data = json.loads(cleaned)
        briefs = data.get("briefs", [])[:max_briefs]
        logger.info("Briefs generated from transcript", extra={"count": len(briefs)})
        return briefs

    except Exception as e:
        logger.error("Brief generation from transcript failed", extra={"error": str(e)})
        return []


def transcribe_vlog(video_path: str, platforms: list = None) -> dict:
    """
    Full pipeline: video → audio → transcript → content briefs.

    Args:
        video_path: path to the vlog video file
        platforms: target platforms for content briefs

    Returns:
        dict with transcript, briefs, and metadata
    """
    audio_path = None
    try:
        # Step 1: Extract audio
        audio_path = extract_audio(video_path)

        # Step 2: Transcribe
        transcript = transcribe_audio(audio_path)

        # Step 3: Generate briefs
        briefs = generate_briefs_from_transcript(transcript, platforms=platforms)

        return {
            "transcript": transcript,
            "briefs": briefs,
            "word_count": len(transcript.split()),
            "video_path": video_path,
            "status": "complete",
        }

    except Exception as e:
        logger.error("Vlog transcription pipeline failed", extra={"error": str(e), "video": video_path})
        return {
            "transcript": "",
            "briefs": [],
            "error": str(e),
            "video_path": video_path,
            "status": "failed",
        }

    finally:
        # Cleanup temp audio file
        if audio_path and os.path.exists(audio_path):
            try:
                os.remove(audio_path)
            except Exception:
                pass

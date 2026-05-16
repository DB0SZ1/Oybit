"""
Vlog Upload API — Accepts video uploads, routes to transcription pipeline,
and returns content briefs generated from the vlog.
"""

import os
import uuid
import shutil
import asyncio
from datetime import datetime
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from backend.content.transcriber import transcribe_vlog
from backend.config import RENDER_OUTPUT_DIR
from backend.logger import get_logger

logger = get_logger("api.vlog_upload")
router = APIRouter()

# In-memory job tracker (production: use DB model VlogTranscriptionJob)
_jobs = {}

ALLOWED_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv", ".webm"}
MAX_FILE_SIZE = 500 * 1024 * 1024  # 500MB


def _process_vlog(job_id: str, video_path: str, platforms: list):
    """Background task to process vlog upload."""
    try:
        _jobs[job_id]["status"] = "processing"
        result = transcribe_vlog(video_path, platforms=platforms)
        _jobs[job_id].update({
            "status": "complete" if result["status"] == "complete" else "failed",
            "transcript": result.get("transcript", ""),
            "briefs": result.get("briefs", []),
            "word_count": result.get("word_count", 0),
            "error": result.get("error"),
            "completed_at": datetime.utcnow().isoformat(),
        })
        logger.info("Vlog processed", extra={"job_id": job_id, "briefs": len(result.get("briefs", []))})
    except Exception as e:
        _jobs[job_id].update({"status": "failed", "error": str(e)})
        logger.error("Vlog processing failed", extra={"job_id": job_id, "error": str(e)})


@router.post("/events/upload-vlog")
async def upload_vlog(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    platforms: str = "linkedin,instagram_personal",
):
    """
    Upload a vlog video for transcription and content brief generation.

    Returns job_id to check status at GET /events/vlog-status/{job_id}
    """
    # Validate file extension
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(400, f"Unsupported format: {ext}. Allowed: {ALLOWED_EXTENSIONS}")

    # Generate job ID and save file
    job_id = str(uuid.uuid4())[:8]
    upload_dir = os.path.join(RENDER_OUTPUT_DIR, "vlog_uploads")
    os.makedirs(upload_dir, exist_ok=True)
    video_path = os.path.join(upload_dir, f"{job_id}{ext}")

    try:
        with open(video_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
    except Exception as e:
        raise HTTPException(500, f"Failed to save upload: {e}")

    file_size = os.path.getsize(video_path)
    if file_size > MAX_FILE_SIZE:
        os.remove(video_path)
        raise HTTPException(400, f"File too large: {file_size / 1024 / 1024:.0f}MB (max {MAX_FILE_SIZE / 1024 / 1024:.0f}MB)")

    # Create job record
    platform_list = [p.strip() for p in platforms.split(",")]
    _jobs[job_id] = {
        "status": "queued",
        "video_path": video_path,
        "platforms": platform_list,
        "created_at": datetime.utcnow().isoformat(),
        "file_size_mb": round(file_size / 1024 / 1024, 1),
    }

    # Process in background
    background_tasks.add_task(_process_vlog, job_id, video_path, platform_list)

    logger.info("Vlog upload accepted", extra={"job_id": job_id, "size_mb": _jobs[job_id]["file_size_mb"]})
    return {"job_id": job_id, "status": "queued"}


@router.get("/events/vlog-status/{job_id}")
async def vlog_status(job_id: str):
    """Check transcription job status."""
    job = _jobs.get(job_id)
    if not job:
        raise HTTPException(404, f"Job {job_id} not found")

    return {
        "job_id": job_id,
        "status": job["status"],
        "briefs": job.get("briefs", []),
        "word_count": job.get("word_count", 0),
        "error": job.get("error"),
        "created_at": job.get("created_at"),
        "completed_at": job.get("completed_at"),
    }

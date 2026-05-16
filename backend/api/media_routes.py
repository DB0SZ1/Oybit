"""
Oybit — Media Library API Routes
Upload, list, delete media assets and assemble manual carousel posts.
"""

import os
import uuid
import json
from datetime import datetime
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional

from backend.db.session import SessionLocal
from backend.db.models import MediaAsset, Post

router = APIRouter(prefix="/api/media", tags=["media"])

MEDIA_DIR = os.getenv("RENDER_OUTPUT_DIR", "output") + "/media_library"

# Ensure directory exists
os.makedirs(MEDIA_DIR, exist_ok=True)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/upload")
async def upload_media(
    file: UploadFile = File(...),
    tags: str = Form("[]"),
    db=Depends(get_db),
):
    """Upload a media file (image/screenshot/testimonial)."""
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Only image files are supported.")

    # Generate unique filename
    ext = os.path.splitext(file.filename or "upload.png")[1]
    unique_name = f"{uuid.uuid4().hex[:12]}{ext}"
    file_path = os.path.join(MEDIA_DIR, unique_name)

    # Save file
    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    # Parse tags
    try:
        tag_list = json.loads(tags)
    except (json.JSONDecodeError, TypeError):
        tag_list = ["untagged"]

    # Save to DB
    asset = MediaAsset(
        filename=unique_name,
        original_name=file.filename or "upload.png",
        tags=tag_list,
        file_size=len(content),
        mime_type=file.content_type,
    )
    db.add(asset)
    db.commit()
    db.refresh(asset)

    return {
        "status": "success",
        "asset": {
            "id": asset.id,
            "filename": asset.filename,
            "original_name": asset.original_name,
            "tags": asset.tags,
            "file_size": asset.file_size,
        },
    }


@router.get("")
def list_media(db=Depends(get_db)):
    """List all uploaded media assets."""
    assets = db.query(MediaAsset).order_by(MediaAsset.uploaded_at.desc()).all()
    return {
        "status": "success",
        "assets": [
            {
                "id": a.id,
                "filename": a.filename,
                "original_name": a.original_name,
                "tags": a.tags or [],
                "uploaded_at": a.uploaded_at.isoformat() if a.uploaded_at else None,
                "file_size": a.file_size,
                "mime_type": a.mime_type,
            }
            for a in assets
        ],
    }


@router.delete("/{asset_id}")
def delete_media(asset_id: int, db=Depends(get_db)):
    """Delete a media asset."""
    asset = db.query(MediaAsset).filter(MediaAsset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    # Delete file from disk
    file_path = os.path.join(MEDIA_DIR, asset.filename)
    if os.path.exists(file_path):
        os.remove(file_path)

    db.delete(asset)
    db.commit()
    return {"status": "success"}


class CarouselRequest(BaseModel):
    asset_ids: List[int]
    caption: Optional[str] = ""
    account: str = "instagram_personal"


@router.post("/carousel")
def create_manual_carousel(payload: CarouselRequest, db=Depends(get_db)):
    """
    Assemble selected media assets into a carousel Post.
    The post enters the pipeline with source='manual' and skips AI generation
    but still goes through Guard + Gate before scheduling.
    """
    if len(payload.asset_ids) < 2:
        raise HTTPException(status_code=400, detail="Need at least 2 images for a carousel.")

    # Fetch the assets in order
    assets = []
    for aid in payload.asset_ids:
        a = db.query(MediaAsset).filter(MediaAsset.id == aid).first()
        if not a:
            raise HTTPException(status_code=404, detail=f"Asset {aid} not found")
        assets.append(a)

    # Build media URLs (relative to static serve path)
    media_urls = [f"/static/media_library/{a.filename}" for a in assets]

    # Determine platform from account
    platform = "instagram"
    if "linkedin" in payload.account:
        platform = "linkedin"
    elif "facebook" in payload.account:
        platform = "facebook"

    # Create the Post record
    post = Post(
        account=payload.account,
        platform=platform,
        format="carousel",
        content_text=payload.caption or "",
        content_preview=payload.caption[:100] if payload.caption else f"Manual carousel ({len(assets)} slides)",
        media_urls=media_urls,
        source="manual",
        status="draft",
    )
    db.add(post)
    db.commit()
    db.refresh(post)

    return {
        "status": "success",
        "post_id": post.id,
        "slides": len(assets),
        "next_step": "Post created as draft. It will go through Guard + Gate before scheduling.",
    }

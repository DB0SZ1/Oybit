from fastapi import APIRouter

router = APIRouter(prefix="/api/media", tags=["Media"])

@router.get("")
def get_media():
    return {"media": []}

@router.post("/upload")
def upload_media():
    return {"status": "uploaded"}

@router.delete("/{media_id}")
def delete_media(media_id: int):
    return {"status": "deleted"}

from fastapi import APIRouter
from app.core.config import settings

router = APIRouter()

@router.get("/health")
def get_health():
    return {"status": "ok", "version": "1.0"}

@router.get("/config")
def get_config():
    return {
        "models": ["tiny", "base", "small", "medium"],
        "default_model": settings.default_model,
        "languages": ["auto", "pt", "en", "es"],
        "max_file_size_mb": settings.max_file_size_mb,
        "max_duration_minutes": settings.max_duration_minutes
    }

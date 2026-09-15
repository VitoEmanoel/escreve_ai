import os
import uuid
import shutil
from pathlib import Path
from fastapi import UploadFile, HTTPException, status
from sqlalchemy.orm import Session
from app.core.config import settings
from app.db.models import TranscriptionJob

AUDIO_EXTENSIONS = {".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg", ".opus"}
VIDEO_EXTENSIONS = {".mp4", ".mov", ".mkv", ".webm", ".avi"}
ALLOWED_MODELS = {"tiny", "base", "small", "medium"}

CHUNK_SIZE = 1024 * 1024  # 1MB chunk

def get_file_extension(filename: str) -> str:
    return Path(filename).suffix.lower()

def create_job(
    db: Session,
    file: UploadFile,
    language: str | None = "auto",
    model: str | None = None,
) -> TranscriptionJob:
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Arquivo inválido ou sem nome."
        )

    ext = get_file_extension(file.filename)
    if ext in AUDIO_EXTENSIONS:
        media_type = "audio"
    elif ext in VIDEO_EXTENSIONS:
        media_type = "video"
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Extensão '{ext}' não suportada. Extensões permitidas: {', '.join(sorted(AUDIO_EXTENSIONS | VIDEO_EXTENSIONS))}"
        )

    model_name = model or settings.default_model
    if model_name not in ALLOWED_MODELS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Modelo '{model_name}' inválido. Modelos permitidos: {', '.join(sorted(ALLOWED_MODELS))}"
        )

    job_id = str(uuid.uuid4())
    upload_dir = Path(settings.data_dir) / "uploads" / job_id
    upload_dir.mkdir(parents=True, exist_ok=True)

    stored_filename = f"input{ext}"
    target_path = upload_dir / stored_filename

    max_bytes = settings.max_file_size_mb * 1024 * 1024
    total_bytes = 0

    try:
        with open(target_path, "wb") as buffer:
            while chunk := file.file.read(CHUNK_SIZE):
                total_bytes += len(chunk)
                if total_bytes > max_bytes:
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"Arquivo excede o limite máximo permitido de {settings.max_file_size_mb} MB."
                    )
                buffer.write(chunk)
    except HTTPException:
        # Clean up created file if too large
        if target_path.exists():
            shutil.rmtree(upload_dir, ignore_errors=True)
        raise
    except Exception as e:
        if target_path.exists():
            shutil.rmtree(upload_dir, ignore_errors=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao salvar o arquivo enviado."
        )

    if total_bytes == 0:
        shutil.rmtree(upload_dir, ignore_errors=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Arquivo enviado está vazio."
        )

    # Validate media with ffprobe
    from app.services.media_service import get_media_info, MediaProcessingError
    
    try:
        duration, has_audio = get_media_info(str(target_path))
    except MediaProcessingError as e:
        shutil.rmtree(upload_dir, ignore_errors=True)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
        
    if not has_audio:
        shutil.rmtree(upload_dir, ignore_errors=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="O arquivo não possui faixa de áudio."
        )
        
    if duration > (settings.max_duration_minutes * 60):
        shutil.rmtree(upload_dir, ignore_errors=True)
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Duração de {duration:.1f}s excede o limite de {settings.max_duration_minutes} minutos."
        )

    job = TranscriptionJob(
        id=job_id,
        original_filename=Path(file.filename).name,
        stored_filename=str(target_path),
        media_type=media_type,
        mime_type=file.content_type or "application/octet-stream",
        file_size_bytes=total_bytes,
        duration_seconds=duration,
        language=language or "auto",
        model_name=model_name,
        status="queued",
        progress=0
    )

    db.add(job)
    db.commit()
    db.refresh(job)
    return job

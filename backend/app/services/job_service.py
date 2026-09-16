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

import subprocess
import json

def get_youtube_info(url: str) -> dict:
    cmd = ["yt-dlp", "-j", url]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Não foi possível obter informações do vídeo do YouTube. Verifique o link."
        )

def create_job(
    db: Session,
    file: UploadFile | None = None,
    youtube_url: str | None = None,
    language: str | None = "auto",
    model: str | None = None,
    task: str | None = "transcribe",
) -> TranscriptionJob:
    if not file and not youtube_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nenhum arquivo ou link do YouTube fornecido."
        )

    model_name = model or settings.default_model
    if model_name not in ALLOWED_MODELS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Modelo '{model_name}' inválido."
        )

    job_id = str(uuid.uuid4())
    upload_dir = Path(settings.data_dir) / "uploads" / job_id
    upload_dir.mkdir(parents=True, exist_ok=True)

    if youtube_url:
        info = get_youtube_info(youtube_url)
        duration = info.get("duration", 0)
        
        if duration > settings.max_duration_minutes * 60:
            shutil.rmtree(upload_dir)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Vídeo muito longo. Máximo permitido: {settings.max_duration_minutes} minutos."
            )
            
        stored_filename = "youtube.mp3"  # Will be downloaded as mp3 in worker
        
        job = TranscriptionJob(
            id=job_id,
            original_filename=youtube_url,
            stored_filename=f"data/uploads/{job_id}/{stored_filename}",
            media_type="youtube",
            mime_type="audio/mp3",
            file_size_bytes=0,
            duration_seconds=duration,
            language=language or "auto",
            model_name=model_name,
            task=task or "transcribe",
            status="queued",
            progress=0
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        return job

    # Handle file upload
    if not file.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Arquivo sem nome.")

    ext = get_file_extension(file.filename)
    if ext in AUDIO_EXTENSIONS:
        media_type = "audio"
    elif ext in VIDEO_EXTENSIONS:
        media_type = "video"
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Extensão '{ext}' não suportada."
        )

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
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Arquivo muito grande. Máximo permitido: {settings.max_file_size_mb} MB"
                    )
                buffer.write(chunk)
    except Exception as e:
        shutil.rmtree(upload_dir, ignore_errors=True)
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao salvar arquivo"
        )

    import subprocess
    cmd = [
        "ffprobe", "-v", "error", "-show_entries",
        "format=duration", "-of",
        "default=noprint_wrappers=1:nokey=1", str(target_path)
    ]
    duration = 0.0
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        duration = float(result.stdout.strip())
        if duration > settings.max_duration_minutes * 60:
            raise ValueError()
    except ValueError:
        shutil.rmtree(upload_dir, ignore_errors=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Arquivo muito longo. Máximo permitido: {settings.max_duration_minutes} minutos"
        )
    except subprocess.CalledProcessError:
        pass

    job = TranscriptionJob(
        id=job_id,
        original_filename=file.filename,
        stored_filename=f"data/uploads/{job_id}/{stored_filename}",
        media_type=media_type,
        mime_type=file.content_type or "application/octet-stream",
        file_size_bytes=total_bytes,
        duration_seconds=duration,
        language=language or "auto",
        model_name=model_name,
        task=task or "transcribe",
        status="queued",
        progress=0
    )
    
    db.add(job)
    db.commit()
    db.refresh(job)
    
    return job

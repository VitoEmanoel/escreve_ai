import json
import shutil
from pathlib import Path
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status, BackgroundTasks, Query
from fastapi.responses import Response, JSONResponse
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models import TranscriptionJob
from app.services import job_service, export_service
from app.schemas.jobs import JobCreateResponse, JobResponse
from app.workers.process_job import process_transcription_job

router = APIRouter()

@router.post("/jobs", response_model=JobCreateResponse, status_code=status.HTTP_202_ACCEPTED)
def create_transcription_job(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    language: str = Form("auto"),
    model: str = Form("base"),
    task: str = Form("transcribe"),
    db: Session = Depends(get_db),
):
    job = job_service.create_job(
        db=db,
        file=file,
        language=language,
        model=model,
    )
    
    # Trigger the background processing
    background_tasks.add_task(process_transcription_job, job.id)
    
    return JobCreateResponse(
        id=job.id,
        status=job.status,
        progress=job.progress
    )

@router.get("/jobs/{job_id}", response_model=JobResponse)
def get_transcription_job(job_id: str, db: Session = Depends(get_db)):
    job = db.query(TranscriptionJob).filter(TranscriptionJob.id == job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job não encontrado."
        )

    segments = None
    if job.segments_json:
        try:
            segments = json.loads(job.segments_json)
        except Exception:
            segments = None

    return JobResponse(
        id=job.id,
        original_filename=job.original_filename,
        media_type=job.media_type,
        mime_type=job.mime_type,
        file_size_bytes=job.file_size_bytes,
        duration_seconds=job.duration_seconds,
        language=job.language,
        model_name=job.model_name,
        status=job.status,
        progress=job.progress,
        error_code=job.error_code,
        error_message=job.error_message,
        full_text=job.full_text,
        segments=segments,
        created_at=job.created_at,
        started_at=job.started_at,
        completed_at=job.completed_at
    )

@router.delete("/jobs/{job_id}", status_code=status.HTTP_200_OK)
def delete_transcription_job(job_id: str, db: Session = Depends(get_db)):
    job = db.query(TranscriptionJob).filter(TranscriptionJob.id == job_id).first()
    if not job:
        return {"message": "Job já excluído ou inexistente."}

    # Remove stored directory and work directory
    if job.stored_filename:
        file_dir = Path(job.stored_filename).parent
        if file_dir.exists():
            shutil.rmtree(file_dir, ignore_errors=True)

    db.delete(job)
    db.commit()
    return {"message": "Job e arquivos associados removidos com sucesso."}

@router.get("/jobs/{job_id}/download")
def download_transcription(
    job_id: str,
    format: str = Query(..., description="Formato desejado: txt, srt, vtt, json"),
    db: Session = Depends(get_db)
):
    job = db.query(TranscriptionJob).filter(TranscriptionJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job não encontrado.")

    if job.status != "completed":
        raise HTTPException(status_code=400, detail="A transcrição ainda não está concluída.")

    if not job.full_text:
        raise HTTPException(status_code=500, detail="Texto da transcrição não encontrado.")

    format = format.lower()
    safe_filename = f"{Path(job.original_filename).stem}.{format}"
    
    segments = []
    if job.segments_json:
        try:
            segments = json.loads(job.segments_json)
        except Exception:
            pass

    if format == "txt":
        content = export_service.generate_txt(job.full_text)
        media_type = "text/plain; charset=utf-8"
    elif format == "srt":
        content = export_service.generate_srt(segments)
        media_type = "text/plain; charset=utf-8"
    elif format == "vtt":
        content = export_service.generate_vtt(segments)
        media_type = "text/vtt; charset=utf-8"
    elif format == "json":
        content = export_service.generate_json(segments, job.full_text, job.language)
        media_type = "application/json; charset=utf-8"
    else:
        raise HTTPException(status_code=400, detail="Formato inválido. Use txt, srt, vtt ou json.")

    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{safe_filename}"'}
    )

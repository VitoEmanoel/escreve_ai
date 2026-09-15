import json
import shutil
from pathlib import Path
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models import TranscriptionJob
from app.services import job_service
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

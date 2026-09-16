import json
import logging
from datetime import datetime
from pathlib import Path
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.db.models import TranscriptionJob
from app.services.media_service import extract_audio, MediaProcessingError
from app.services.transcription_service import transcription_service

logger = logging.getLogger(__name__)

def process_transcription_job(job_id: str):
    db: Session = SessionLocal()
    try:
        job = db.query(TranscriptionJob).filter(TranscriptionJob.id == job_id).first()
        if not job:
            logger.error(f"Job {job_id} not found.")
            return

        if job.status != "queued":
            logger.warning(f"Job {job_id} is not queued. Current status: {job.status}")
            return

        # Mark as processing
        job.status = "processing"
        job.started_at = datetime.utcnow()
        job.progress = 10
        db.commit()

        # Step 1: Extract/Normalize Audio
        original_path = job.stored_filename
        job_dir = Path(original_path).parent
        wav_path = str(job_dir / "audio.wav")
        
        if job.media_type == "youtube":
            from app.services.media_service import download_youtube_audio
            logger.info(f"Downloading YouTube audio for job {job_id}...")
            job.progress = 15
            db.commit()
            # Note: original_filename contains the youtube URL in this case
            download_youtube_audio(job.original_filename, original_path)

        logger.info(f"Extracting/Normalizing audio for job {job_id}...")
        job.progress = 20
        db.commit()
        
        extract_audio(original_path, wav_path)
        
        # Step 2: Transcribe
        logger.info(f"Starting transcription for job {job_id}...")
        job.progress = 50
        db.commit()
        
        result = transcription_service.transcribe(
            audio_path=wav_path,
            language=job.language,
            model_name=job.model_name,
            task=job.task
        )
        
        # Step 3: Save results
        job.full_text = result.text
        job.segments_json = json.dumps(result.segments, ensure_ascii=False)
        job.language = result.language
        
        job.progress = 100
        job.status = "completed"
        job.completed_at = datetime.utcnow()
        db.commit()
        logger.info(f"Job {job_id} completed successfully.")

    except MediaProcessingError as e:
        logger.error(f"Media processing error on job {job_id}: {str(e)}")
        job.status = "failed"
        job.error_message = "Erro ao processar o arquivo de mídia."
        db.commit()
    except Exception as e:
        logger.exception(f"Unexpected error on job {job_id}: {str(e)}")
        job.status = "failed"
        job.error_message = "Erro interno durante o processamento da transcrição."
        db.commit()
    finally:
        db.close()

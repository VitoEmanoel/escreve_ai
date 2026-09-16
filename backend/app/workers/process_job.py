import json
import logging
import threading
from datetime import datetime
from pathlib import Path
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.db.models import TranscriptionJob
from app.services.media_service import extract_audio, MediaProcessingError
from app.services.transcription_service import transcription_service

logger = logging.getLogger(__name__)

job_lock = threading.Lock()

def process_transcription_job(job_id: str):
    # Aguarda a liberação do lock para que os uploads em lote processem sequencialmente (evita OOM)
    with job_lock:
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
            
            def update_progress(percent: int):
                # Scale from 50 to 99% for transcription phase
                scaled_percent = 50 + int((percent / 100.0) * 49)
                if job.progress != scaled_percent:
                    job.progress = scaled_percent
                    db.commit()

            result = transcription_service.transcribe(
                audio_path=wav_path,
                language=job.language,
                model_name=job.model_name,
                task=job.task,
                diarize=bool(job.diarize),
                duration_seconds=job.duration_seconds or 0.0,
                progress_callback=update_progress
            )
            
            # Step 3: Save results
            logger.info(f"Transcription complete for job {job_id}")
            job.full_text = result.text
            job.segments_json = json.dumps(result.segments)
            job.language = result.language # in case it was auto
            job.status = "completed"
            job.progress = 100
            job.completed_at = datetime.utcnow()
            db.commit()
            
        except MediaProcessingError as e:
            logger.error(f"Media processing error for job {job_id}: {str(e)}")
            job.status = "failed"
            job.error_message = str(e)
            job.error_code = "MEDIA_ERROR"
            db.commit()
            
        except Exception as e:
            logger.error(f"Unexpected error for job {job_id}: {str(e)}", exc_info=True)
            job.status = "failed"
            job.error_message = f"Erro interno: {str(e)}"
            job.error_code = "INTERNAL_ERROR"
            db.commit()
            
        finally:
            db.close()

import logging
import shutil
import asyncio
from datetime import datetime, timedelta
from app.db.session import SessionLocal
from app.db.models import TranscriptionJob
from app.core.config import settings

logger = logging.getLogger(__name__)

async def cleanup_old_jobs_loop():
    while True:
        try:
            logger.info("Executando limpeza periódica de jobs antigos...")
            db = SessionLocal()
            cutoff = datetime.utcnow() - timedelta(hours=settings.job_retention_hours)
            
            old_jobs = db.query(TranscriptionJob).filter(TranscriptionJob.created_at < cutoff).all()
            
            for job in old_jobs:
                logger.info(f"Removendo job expirado: {job.id}")
                # Remove files
                if job.stored_filename:
                    job_dir = job.stored_filename.rsplit("/", 1)[0]
                    shutil.rmtree(job_dir, ignore_errors=True)
                # Remove from DB
                db.delete(job)
            
            db.commit()
            db.close()
        except Exception as e:
            logger.error(f"Erro na rotina de limpeza: {e}")
            
        # Sleep for 1 hour
        await asyncio.sleep(3600)

from sqlalchemy import Column, String, Integer, Float, DateTime, Text, Enum
from app.db.session import Base
from datetime import datetime
import uuid

class TranscriptionJob(Base):
    __tablename__ = "transcription_jobs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    original_filename = Column(String, nullable=False)
    stored_filename = Column(String, nullable=False)
    media_type = Column(String, nullable=False) # 'audio' or 'video'
    mime_type = Column(String, nullable=False)
    file_size_bytes = Column(Integer, nullable=False)
    duration_seconds = Column(Float, nullable=True)
    language = Column(String, nullable=True)
    model_name = Column(String, nullable=False)
    status = Column(String, nullable=False, default="queued") # queued, processing, completed, failed, cancelled
    progress = Column(Integer, default=0)
    error_code = Column(String, nullable=True)
    error_message = Column(String, nullable=True)
    full_text = Column(Text, nullable=True)
    segments_json = Column(Text, nullable=True) # Text storing JSON
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)

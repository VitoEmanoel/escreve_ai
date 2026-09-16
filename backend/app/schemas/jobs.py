from pydantic import BaseModel
from typing import Optional, List, Any
from datetime import datetime

class JobCreateResponse(BaseModel):
    id: str
    status: str
    progress: int

class JobResponse(BaseModel):
    id: str
    original_filename: str
    media_type: str
    mime_type: str
    file_size_bytes: int
    duration_seconds: Optional[float] = None
    language: Optional[str] = None
    model_name: str
    task: str
    status: str
    progress: int
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    full_text: Optional[str] = None
    segments: Optional[Any] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    model_config = {
        "from_attributes": True,
        "protected_namespaces": (),
    }

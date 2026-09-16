import logging
from faster_whisper import WhisperModel
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from app.core.config import settings

logger = logging.getLogger(__name__)

class TranscriptionResult(BaseModel):
    language: str
    language_probability: float
    segments: List[Dict[str, Any]]
    text: str

class TranscriptionService:
    def __init__(self):
        self._models = {}
        
        self.device = settings.whisper_device
        self.compute_type = settings.whisper_compute_type if settings.whisper_compute_type != "auto" else "default"
        logger.info(f"TranscriptionService initialized with device: {self.device}, compute_type: {self.compute_type}")

    def _get_model(self, model_name: str) -> WhisperModel:
        if model_name not in self._models:
            logger.info(f"Loading Whisper model '{model_name}' on {self.device}...")
            self._models[model_name] = WhisperModel(
                model_name,
                device=self.device,
                compute_type=self.compute_type
            )
        return self._models[model_name]

    def transcribe(
        self,
        audio_path: str,
        language: str | None,
        model_name: str,
        task: str = "transcribe"
    ) -> TranscriptionResult:
        model = self._get_model(model_name)
        
        # If language is "auto", pass None to faster-whisper for auto-detection
        whisper_lang = None if language == "auto" else language
        
        logger.info(f"Starting transcription of {audio_path} using model {model_name}")
        segments_generator, info = model.transcribe(
            audio_path,
            language=whisper_lang,
            task=task,
            beam_size=5
        )
        
        segments = []
        full_text_parts = []
        
        for segment in segments_generator:
            segment_dict = {
                "id": segment.id,
                "start": segment.start,
                "end": segment.end,
                "text": segment.text.strip()
            }
            segments.append(segment_dict)
            full_text_parts.append(segment.text.strip())
            
        full_text = " ".join(full_text_parts)
        
        return TranscriptionResult(
            language=info.language,
            language_probability=info.language_probability,
            segments=segments,
            text=full_text
        )

# Singleton instance
transcription_service = TranscriptionService()

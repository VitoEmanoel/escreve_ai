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
        task: str = "transcribe",
        diarize: bool = False,
        duration_seconds: float = 0.0,
        progress_callback = None
    ) -> TranscriptionResult:
        import os
        model = self._get_model(model_name)
        
        whisper_lang = None if language == "auto" else language
        
        logger.info(f"Starting transcription of {audio_path} using model {model_name}")
        segments_generator, info = model.transcribe(
            audio_path,
            language=whisper_lang,
            task=task,
            beam_size=5,
            word_timestamps=diarize
        )
        
        segments = []
        full_text_parts = []
        
        for segment in segments_generator:
            segment_dict = {
                "id": segment.id,
                "start": segment.start,
                "end": segment.end,
                "text": segment.text.strip(),
            }
            if diarize and hasattr(segment, 'words'):
                segment_dict["words"] = [{"start": w.start, "end": w.end, "word": w.word} for w in segment.words]
            segments.append(segment_dict)
            full_text_parts.append(segment.text.strip())
            
            if progress_callback and duration_seconds > 0:
                percent = min(99, int((segment.end / duration_seconds) * 100))
                progress_callback(percent)
                
        # Perform Diarization if requested
        if diarize:
            hf_token = os.environ.get("HF_TOKEN")
            if not hf_token:
                logger.error("HF_TOKEN is required for diarization. Skipping diarization.")
            else:
                try:
                    logger.info("Running pyannote.audio speaker diarization...")
                    import torch
                    from pyannote.audio import Pipeline
                    # Initialize the pipeline
                    pipeline = Pipeline.from_pretrained("pyannote/speaker-diarization-3.1", use_auth_token=hf_token)
                    pipeline.to(torch.device(self.device if self.device == "cuda" else "cpu"))
                    
                    # Run the pipeline on the audio
                    diarization_result = pipeline(audio_path)
                    
                    # Assign speakers to each word
                    for segment_dict in segments:
                        if "words" in segment_dict:
                            speaker_counts = {}
                            for w in segment_dict["words"]:
                                # Find intersection for this word
                                w_start, w_end = w["start"], w["end"]
                                w_speaker = "UNKNOWN"
                                best_intersection = 0.0
                                for turn, _, speaker in diarization_result.itertracks(yield_label=True):
                                    overlap = max(0, min(w_end, turn.end) - max(w_start, turn.start))
                                    if overlap > best_intersection:
                                        best_intersection = overlap
                                        w_speaker = speaker
                                w["speaker"] = w_speaker
                                speaker_counts[w_speaker] = speaker_counts.get(w_speaker, 0) + 1
                            
                            # Assign the most frequent speaker to the segment
                            if speaker_counts:
                                segment_dict["speaker"] = max(speaker_counts, key=speaker_counts.get)
                            else:
                                segment_dict["speaker"] = "UNKNOWN"
                            
                            # Optionally delete words to save space if you don't need them
                            # del segment_dict["words"]
                except Exception as e:
                    logger.error(f"Diarization failed: {e}")

        full_text = " ".join(full_text_parts)
        
        return TranscriptionResult(
            language=info.language,
            language_probability=info.language_probability,
            segments=segments,
            text=full_text
        )

# Singleton instance
transcription_service = TranscriptionService()

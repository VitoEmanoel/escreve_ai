import json
import subprocess
import logging
from typing import Dict, Any, Tuple
from fastapi import HTTPException, status
from app.core.config import settings

logger = logging.getLogger(__name__)

class MediaProcessingError(Exception):
    pass

def get_media_info(file_path: str) -> Tuple[float, bool]:
    """
    Uses ffprobe to analyze the media file.
    Returns a tuple of (duration_in_seconds, has_audio_stream).
    """
    cmd = [
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration",
        "-show_streams",
        "-print_format", "json",
        file_path
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30, check=True)
        probe = json.loads(result.stdout)
        
        # Check streams for audio
        streams = probe.get("streams", [])
        has_audio = any(stream.get("codec_type") == "audio" for stream in streams)
        
        # Get duration
        format_info = probe.get("format", {})
        duration_str = format_info.get("duration", "0")
        try:
            duration = float(duration_str)
        except ValueError:
            duration = 0.0
            
        return duration, has_audio

    except subprocess.TimeoutExpired:
        logger.error(f"ffprobe timeout for {file_path}")
        raise MediaProcessingError("Tempo limite excedido ao analisar o arquivo de mídia.")
    except subprocess.CalledProcessError as e:
        logger.error(f"ffprobe failed for {file_path}. Stderr: {e.stderr}")
        raise MediaProcessingError("Falha ao analisar o arquivo de mídia.")
    except json.JSONDecodeError:
        logger.error(f"Failed to parse ffprobe output for {file_path}")
        raise MediaProcessingError("Saída inválida da análise de mídia.")
    except FileNotFoundError:
        logger.error("ffprobe not found on the system")
        raise MediaProcessingError("A ferramenta 'ffprobe' não está instalada no sistema.")


def extract_audio(input_path: str, output_path: str) -> None:
    """
    Extracts audio from video or normalizes audio using FFmpeg.
    Outputs a mono, 16kHz, pcm_s16le WAV file.
    """
    cmd = [
        "ffmpeg",
        "-y",               # Overwrite output files without asking
        "-i", input_path,
        "-vn",              # Disable video
        "-ac", "1",         # Set audio channels to mono
        "-ar", "16000",     # Set audio sampling rate to 16kHz
        "-c:a", "pcm_s16le",# Set audio codec to PCM 16-bit little-endian
        output_path
    ]
    
    try:
        # We give a longer timeout for extraction
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600, check=True)
    except subprocess.TimeoutExpired:
        logger.error(f"ffmpeg timeout for {input_path}")
        raise MediaProcessingError("Tempo limite excedido ao processar o áudio.")
    except subprocess.CalledProcessError as e:
        logger.error(f"ffmpeg failed for {input_path}. Stderr: {e.stderr}")
        raise MediaProcessingError("Falha na extração ou normalização do áudio.")
    except FileNotFoundError:
        logger.error("ffmpeg not found on the system")
        raise MediaProcessingError("A ferramenta 'ffmpeg' não está instalada no sistema.")

def download_youtube_audio(url: str, output_path: str) -> None:
    """
    Downloads audio from YouTube using yt-dlp.
    """
    cmd = [
        "yt-dlp",
        "--extract-audio",
        "--audio-format", "mp3",
        "--audio-quality", "5",
        "-o", output_path,
        url
    ]
    try:
        subprocess.run(cmd, capture_output=True, text=True, timeout=1200, check=True)
    except subprocess.TimeoutExpired:
        logger.error(f"yt-dlp timeout for {url}")
        raise MediaProcessingError("Tempo limite excedido ao baixar o áudio do YouTube.")
    except subprocess.CalledProcessError as e:
        logger.error(f"yt-dlp failed for {url}. Stderr: {e.stderr}")
        raise MediaProcessingError("Falha ao baixar o áudio do YouTube. Verifique se o link é válido.")
    except FileNotFoundError:
        logger.error("yt-dlp not found on the system")
        raise MediaProcessingError("A ferramenta 'yt-dlp' não está instalada no sistema.")

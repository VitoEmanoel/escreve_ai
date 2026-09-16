import json
from typing import List, Dict, Any

def format_timestamp(seconds: float, separator: str = ",") -> str:
    """
    Format seconds to HH:MM:SS,mmm (SRT) or HH:MM:SS.mmm (VTT)
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int(round((seconds - int(seconds)) * 1000))
    
    # Handle rounding edge case where millis might be 1000
    if millis == 1000:
        secs += 1
        millis = 0
        if secs == 60:
            secs = 0
            minutes += 1
            if minutes == 60:
                minutes = 0
                hours += 1
                
    return f"{hours:02d}:{minutes:02d}:{secs:02d}{separator}{millis:03d}"

def generate_srt(segments: List[Dict[str, Any]]) -> str:
    lines = []
    for i, seg in enumerate(segments, start=1):
        start_ts = format_timestamp(seg["start"], separator=",")
        end_ts = format_timestamp(seg["end"], separator=",")
        speaker = seg.get("speaker")
        text = f"{speaker}: {seg['text'].strip()}" if speaker else seg['text'].strip()
        lines.append(str(i))
        lines.append(f"{start_ts} --> {end_ts}")
        lines.append(text)
        lines.append("")
    return "\n".join(lines)

def generate_vtt(segments: List[Dict[str, Any]]) -> str:
    lines = ["WEBVTT", ""]
    for seg in segments:
        start_ts = format_timestamp(seg["start"], separator=".")
        end_ts = format_timestamp(seg["end"], separator=".")
        speaker = seg.get("speaker")
        text = f"<{speaker}> {seg['text'].strip()}" if speaker else seg['text'].strip()
        lines.append(f"{start_ts} --> {end_ts}")
        lines.append(text)
        lines.append("")
    return "\n".join(lines)

def generate_txt(full_text: str, segments: List[Dict[str, Any]] = None) -> str:
    if segments and any("speaker" in s for s in segments):
        lines = []
        for s in segments:
            speaker = s.get("speaker", "Locutor")
            lines.append(f"{speaker}: {s['text']}")
        return "\n".join(lines)
    return full_text

def generate_json(segments: List[Dict[str, Any]], full_text: str, language: str) -> str:
    data = {
        "language": language,
        "text": full_text,
        "segments": segments
    }
    return json.dumps(data, ensure_ascii=False, indent=2)

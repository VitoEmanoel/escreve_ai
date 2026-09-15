from app.services.export_service import format_timestamp, generate_srt, generate_vtt

def test_format_timestamp():
    # 0 seconds
    assert format_timestamp(0, ",") == "00:00:00,000"
    # 1.5 seconds
    assert format_timestamp(1.5, ",") == "00:00:01,500"
    # 1 hour, 1 minute, 1.001 seconds
    assert format_timestamp(3661.001, ".") == "01:01:01.001"
    # Rounding edge case
    assert format_timestamp(0.9999, ",") == "00:00:01,000"

def test_generate_srt():
    segments = [
        {"start": 0.0, "end": 1.5, "text": "Olá mundo"}
    ]
    srt = generate_srt(segments)
    assert "1" in srt
    assert "00:00:00,000 --> 00:00:01,500" in srt
    assert "Olá mundo" in srt

def test_generate_vtt():
    segments = [
        {"start": 0.0, "end": 1.5, "text": "Olá mundo"}
    ]
    vtt = generate_vtt(segments)
    assert vtt.startswith("WEBVTT")
    assert "00:00:00.000 --> 00:00:01.500" in vtt
    assert "Olá mundo" in vtt

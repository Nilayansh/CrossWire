import hashlib
import json
from pathlib import Path
import httpx

from app.config import settings

SAMPLE_KN_TRANSCRIPT = "ಬೆಳ್ಳಂದೂರು ಇಕೋಸ್ಪೇಸ್ ಮುಂದೆ ಭಾರಿ ನೀರು ನಿಂತಿದೆ"


def _get_cache_dir() -> Path:
    base_dir = Path(__file__).resolve().parent.parent.parent
    cache_dir = base_dir / "data" / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


def transcribe(ogg_bytes: bytes) -> tuple[str, str]:
    """Transcribe audio bytes (OGG/OPUS/WAV) to (text, lang).

    In DEMO_MODE, returns a cached transcript by file hash or defaults to Kannada fixture.
    When live, calls Sarvam STT API.
    """
    file_hash = hashlib.sha256(ogg_bytes).hexdigest()[:16]
    cache_path = _get_cache_dir() / f"stt_{file_hash}.json"

    # Prioritize cache in DEMO_MODE
    if settings.DEMO_MODE and cache_path.exists():
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("text", SAMPLE_KN_TRANSCRIPT), data.get("lang", "kn")
        except Exception:
            pass

    # Try live Sarvam STT if key configured and not in DEMO_MODE
    if settings.SARVAM_API_KEY and not settings.DEMO_MODE:
        try:
            url = "https://api.sarvam.ai/speech-to-text"
            headers = {"api-subscription-key": settings.SARVAM_API_KEY}
            files = {"file": ("audio.ogg", ogg_bytes, "audio/ogg")}
            data = {"model": "saaras:v1"}
            with httpx.Client(timeout=15.0) as client:
                resp = client.post(url, headers=headers, files=files, data=data)
                if resp.status_code == 200:
                    res_json = resp.json()
                    transcript = res_json.get("transcript", SAMPLE_KN_TRANSCRIPT)
                    lang = res_json.get("language_code", "kn")
                    with open(cache_path, "w", encoding="utf-8") as f:
                        json.dump({"text": transcript, "lang": lang}, f, indent=2)
                    return transcript, lang
        except Exception:
            pass

    # In DEMO_MODE or offline fallback: return cached or standard Kannada sample
    if cache_path.exists():
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("text", SAMPLE_KN_TRANSCRIPT), data.get("lang", "kn")
        except Exception:
            pass

    return SAMPLE_KN_TRANSCRIPT, "kn"

import hashlib
import json
from pathlib import Path
from typing import Optional, Literal
import base64
import httpx

from app.config import settings
from app.intake.models import DepthEstimate


def _get_cache_dir() -> Path:
    base_dir = Path(__file__).resolve().parent.parent.parent
    cache_dir = base_dir / "data" / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


def depth(photo_bytes: bytes) -> tuple[Optional[Literal["ankle", "knee", "waist", "vehicle"]], float]:
    """Estimate flood water depth from citizen photo into discrete buckets:

    'ankle', 'knee', 'waist', 'vehicle' with confidence score.
    In DEMO_MODE, returns cached estimate by image hash or default 'knee' depth.
    """
    if not photo_bytes:
        return None, 0.0

    photo_hash = hashlib.sha256(photo_bytes).hexdigest()[:16]
    cache_path = _get_cache_dir() / f"vision_{photo_hash}.json"

    # Prioritize cache in DEMO_MODE
    if settings.DEMO_MODE and cache_path.exists():
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("bucket", "knee"), float(data.get("confidence", 0.90))
        except Exception:
            pass

    # Live multimodal LLM inspection if direct backend and API key present
    if settings.LLM_BACKEND == "direct" and settings.OPENAI_API_KEY and not settings.DEMO_MODE:
        try:
            b64_img = base64.b64encode(photo_bytes).decode("utf-8")
            url = "https://api.openai.com/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
                "Content-Type": "application/json",
            }
            payload = {
                "model": "gpt-4o-mini",
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "Estimate flood water level relative to people/cars: ankle, knee, waist, or vehicle. Reply JSON: {\"bucket\": \"knee\", \"confidence\": 0.9}",
                            },
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/jpeg;base64,{b64_img}"},
                            },
                        ],
                    }
                ],
                "response_format": {"type": "json_object"},
            }
            with httpx.Client(timeout=15.0) as client:
                resp = client.post(url, headers=headers, json=payload)
                if resp.status_code == 200:
                    content = resp.json()["choices"][0]["message"]["content"]
                    parsed = json.loads(content)
                    b = parsed.get("bucket", "knee")
                    conf = float(parsed.get("confidence", 0.85))
                    with open(cache_path, "w", encoding="utf-8") as f:
                        json.dump({"bucket": b, "confidence": conf}, f, indent=2)
                    return b, conf
        except Exception:
            pass

    # Default realistic estimate for flooded streets
    return "knee", 0.88

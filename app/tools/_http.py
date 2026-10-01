import hashlib
import json
from pathlib import Path
from typing import Optional, Any
import httpx

from app.config import settings


def _get_cache_dir() -> Path:
    base_dir = Path(__file__).resolve().parent.parent.parent
    cache_dir = base_dir / "data" / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


def _compute_cache_key(url: str, params: Optional[dict] = None, explicit_key: Optional[str] = None) -> str:
    if explicit_key:
        return explicit_key.replace(".json", "")
    serialized = f"{url}_{sorted(params.items()) if params else ''}"
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()[:16]


def get_json(
    url: str,
    params: Optional[dict] = None,
    cache_key: Optional[str] = None,
    headers: Optional[dict] = None,
    timeout: float = 10.0,
) -> dict[str, Any]:
    """HTTP client wrapper with offline caching for DEMO_MODE and fallback support.

    If DEMO_MODE is True, reads cached JSON from data/cache/<key>.json.
    If network is enabled or cache is missing, queries external URL and caches response.
    """
    key = _compute_cache_key(url, params, cache_key)
    cache_path = _get_cache_dir() / f"{key}.json"

    # In DEMO_MODE, prioritize cached files
    if settings.DEMO_MODE and cache_path.exists():
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass

    # Try live HTTP request
    try:
        with httpx.Client(timeout=timeout) as client:
            resp = client.get(url, params=params, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                # Update cache
                try:
                    with open(cache_path, "w", encoding="utf-8") as f:
                        json.dump(data, f, indent=2)
                except Exception:
                    pass
                return data
    except Exception:
        # Fallback to cache if live request fails
        if cache_path.exists():
            with open(cache_path, "r", encoding="utf-8") as f:
                return json.load(f)

    # If cache still exists after any non-200 live response
    if cache_path.exists():
        with open(cache_path, "r", encoding="utf-8") as f:
            return json.load(f)

    return {}


def save_cache(cache_key: str, data: Any) -> None:
    """Explicitly save data into the cache folder."""
    cache_dir = _get_cache_dir()
    clean_key = cache_key.replace(".json", "")
    cache_path = cache_dir / f"{clean_key}.json"
    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

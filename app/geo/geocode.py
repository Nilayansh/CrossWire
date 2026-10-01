import csv
import os
import re
from pathlib import Path
from typing import Optional
from rapidfuzz import fuzz


class Landmark:
    def __init__(self, name: str, lat: float, lon: float, pincode: str, aliases: list[str]):
        self.name = name
        self.lat = lat
        self.lon = lon
        self.pincode = pincode
        self.aliases = aliases

    @property
    def all_names(self) -> list[str]:
        return [self.name] + self.aliases


_LANDMARKS_CACHE: Optional[list[Landmark]] = None


def _get_landmarks_csv_path() -> Path:
    base_dir = Path(__file__).resolve().parent.parent.parent
    return base_dir / "data" / "landmarks.csv"


def load_landmarks(csv_path: Optional[Path] = None) -> list[Landmark]:
    global _LANDMARKS_CACHE
    if _LANDMARKS_CACHE is not None and csv_path is None:
        return _LANDMARKS_CACHE

    target_path = csv_path or _get_landmarks_csv_path()
    landmarks: list[Landmark] = []
    if target_path.exists():
        with open(target_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                name = row.get("name", "").strip()
                lat = float(row.get("lat", 0.0))
                lon = float(row.get("lon", 0.0))
                pincode = row.get("pincode", "").strip()
                raw_aliases = row.get("aliases", "").strip()
                aliases = [a.strip() for a in raw_aliases.split("|") if a.strip()] if raw_aliases else []
                if name:
                    landmarks.append(Landmark(name, lat, lon, pincode, aliases))

    if csv_path is None:
        _LANDMARKS_CACHE = landmarks
    return landmarks


def geocode(
    text: str,
    pin: Optional[str] = None,
    csv_path: Optional[Path] = None,
) -> tuple[float, float, float]:
    """Geocode an input text and/or pincode to (latitude, longitude, confidence).

    Order of resolution:
    1. Direct pin match if provided.
    2. Embedded 6-digit pin code in text.
    3. Fuzzy match against landmarks.csv via rapidfuzz.
    4. Fallback to Bangalore central coordinates with low confidence.
    """
    landmarks = load_landmarks(csv_path)

    # 1. Direct pin match if provided
    if pin:
        pin_cleaned = pin.strip()
        for lm in landmarks:
            if lm.pincode and lm.pincode == pin_cleaned:
                return (lm.lat, lm.lon, 0.95)

    # 2. Extract 6-digit pin code from text (e.g., 560xxx)
    pin_match = re.search(r"\b(56\d{4})\b", text)
    if pin_match:
        extracted_pin = pin_match.group(1)
        for lm in landmarks:
            if lm.pincode and lm.pincode == extracted_pin:
                return (lm.lat, lm.lon, 0.90)

    # 3. Fuzzy matching on landmark names and aliases
    text_lower = text.lower().strip()
    best_match: Optional[Landmark] = None
    best_score: float = 0.0

    for lm in landmarks:
        for candidate in lm.all_names:
            c_lower = candidate.lower().strip()
            # Combine partial ratio and token set ratio for robust substring and token matching
            score = max(
                fuzz.partial_ratio(c_lower, text_lower),
                fuzz.token_set_ratio(c_lower, text_lower),
            )
            if score > best_score:
                best_score = score
                best_match = lm

    if best_match and best_score >= 80:
        confidence = min(0.95, round(best_score / 100.0, 2))
        return (best_match.lat, best_match.lon, confidence)
    elif best_match and best_score >= 55:
        confidence = round((best_score / 100.0) * 0.75, 2)
        return (best_match.lat, best_match.lon, confidence)

    # 4. Fallback to Bangalore centroid
    return (12.9716, 77.5946, 0.20)

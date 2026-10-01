import re
import uuid
from datetime import datetime, timezone
from typing import Optional
import httpx

from app.contracts.models import Ticket
from app.config import settings
from app.geo.h3_utils import latlon_to_cell
from app.geo.geocode import geocode
from app.intake.models import RawInput, TicketDraft
from app.intake.stt import transcribe
from app.intake.vision import depth

KNOWN_TRANSLATIONS: dict[str, str] = {
    "ಬೆಳ್ಳಂದೂರು ಇಕೋಸ್ಪೇಸ್ ಮುಂದೆ ಭಾರಿ ನೀರು ನಿಂತಿದೆ": "Heavy water accumulation in front of Bellandur Ecospace",
    "ವಿದ್ಯುತ್ ಕಂಬದಿಂದ ಕಿಡಿ ಬರುತ್ತಿದೆ ಮತ್ತು ಕರೆಂಟ್ ಹೋಗಿದೆ": "Sparks from electric pole and power has gone off",
    "ವಾಹನಗಳು ನೀರಿನಲ್ಲಿ ಸಿಲುಕಿಕೊಂಡಿವೆ, ದಯವಿಟ್ಟು ಸಹಾಯ ಮಾಡಿ": "Vehicles are stranded in water, please help",
    "ಅಪಾರ್ಟ್ಮೆಂಟ್ ಬೇಸ್ಮೆಂಟ್ಗೆ ನೀರು ನುಗ್ಗುತ್ತಿದೆ": "Water entering apartment basement",
}


def is_kannada(text: str) -> bool:
    """Check if string contains Kannada unicode characters."""
    return bool(re.search(r"[\u0c80-\u0cff]", text))


def translate(text: str, source_lang: str = "kn") -> str:
    """Translate non-English citizen text to English.

    In DEMO_MODE or without Sarvam API credentials, uses canonical phrasebook.
    """
    if source_lang == "en" or not is_kannada(text):
        return text

    # Check known phrasebook
    for kn_phrase, en_trans in KNOWN_TRANSLATIONS.items():
        if kn_phrase in text or text in kn_phrase:
            return en_trans

    # Live translation via Sarvam Translate API if available
    if settings.SARVAM_API_KEY and not settings.DEMO_MODE:
        try:
            url = "https://api.sarvam.ai/translate"
            headers = {"api-subscription-key": settings.SARVAM_API_KEY}
            payload = {
                "input": text,
                "source_language_code": source_lang,
                "target_language_code": "en-IN",
                "mode": "formal",
            }
            with httpx.Client(timeout=10.0) as client:
                resp = client.post(url, headers=headers, json=payload)
                if resp.status_code == 200:
                    return resp.json().get("translated_text", text)
        except Exception:
            pass

    # Heuristic fallback for Bellandur Ecospace if text has ecospace
    if "ಇಕೋಸ್ಪೇಸ್" in text or "ಬೆಳ್ಳಂದೂರು" in text:
        return "Heavy water accumulation in front of Bellandur Ecospace"

    return text


def extract_draft(text_en: str, llm=None) -> TicketDraft:
    """Extract category, severity, and location hint via LLM or rule-based fallback."""
    if llm is not None:
        try:
            return llm.structured(
                TicketDraft,
                prompt=f"Extract ticket details from citizen complaint: {text_en}",
                tier="fast",
            )
        except Exception:
            pass

    # Deterministic rule-based extraction
    t_lower = text_en.lower()

    if any(w in t_lower for w in ["water", "flood", "waterlogging", "rain", "overflowing", "submerged"]):
        cat = "waterlogging"
        sev = 5 if ("basement" in t_lower or "heavy" in t_lower or "waist" in t_lower) else 4
    elif any(w in t_lower for w in ["power", "electric", "spark", "outage", "pole", "blackout", "feeder"]):
        cat = "power"
        sev = 4
    elif any(w in t_lower for w in ["sewage", "manhole", "drain", "gutter", "foul"]):
        cat = "sewage"
        sev = 4
    elif any(w in t_lower for w in ["traffic", "stalled", "stuck", "jam", "stranded", "vehicle"]):
        cat = "traffic"
        sev = 5 if ("stranded" in t_lower or "2 km" in t_lower) else 3
    elif any(w in t_lower for w in ["debris", "garbage", "trash", "waste", "dump"]):
        cat = "garbage_debris"
        sev = 3
    elif any(w in t_lower for w in ["road", "pothole", "cracked", "damage"]):
        cat = "road_damage"
        sev = 3
    elif any(w in t_lower for w in ["pipe", "leak", "drinking water", "supply"]):
        cat = "water_supply"
        sev = 3
    else:
        cat = "other"
        sev = 3

    return TicketDraft(
        category=cat,
        severity=sev,
        location_hint=text_en,
        text_en=text_en,
    )


def to_ticket(raw: RawInput, llm=None) -> Ticket:
    """Normalize a RawInput submission into a fully validated Ticket object."""
    # 1. Resolve speech-to-text if audio bytes provided
    if raw.voice_bytes:
        orig_text, lang = transcribe(raw.voice_bytes)
    elif raw.text:
        orig_text = raw.text.strip()
        lang = "kn" if is_kannada(orig_text) else "en"
    else:
        orig_text = "Waterlogging reported"
        lang = "en"

    # 2. Translate if Kannada
    text_en = translate(orig_text, source_lang=lang)

    # 3. LLM structured extraction for category & severity
    draft = extract_draft(text_en, llm=llm)

    # 4. Geocode
    if raw.lat is not None and raw.lon is not None:
        lat = raw.lat
        lon = raw.lon
        conf = 0.95
    else:
        lat, lon, conf = geocode(text=text_en, pin=raw.pin)

    # 5. H3 cell conversion
    h3_cell = latlon_to_cell(lat, lon, res=8)

    # 6. Vision depth estimation
    photo_depth_bucket = None
    if raw.photo_bytes:
        photo_depth_bucket, _ = depth(raw.photo_bytes)

    ticket_id = f"t-{uuid.uuid4().hex[:6]}"
    ts = raw.ts or datetime.now(timezone.utc)
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)

    return Ticket(
        id=ticket_id,
        ts=ts,
        channel=raw.channel,
        lang=lang,
        text_original=orig_text,
        text_en=text_en,
        category=draft.category,
        severity=draft.severity,
        lat=round(lat, 4),
        lon=round(lon, 4),
        geo_confidence=round(conf, 2),
        h3_r8=h3_cell,
        photo_depth=photo_depth_bucket,
        reporter_chat_id=raw.reporter_chat_id,
        is_synthetic=(raw.channel == "synthetic"),
    )

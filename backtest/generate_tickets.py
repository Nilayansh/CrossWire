from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import random
from typing import Optional

from app.contracts.models import Ticket

SAMPLE_LOCALITIES = [
    {"name": "Bellandur Ecospace", "lat": 12.926, "lon": 77.683, "h3": "886189255bfffff"},
    {"name": "Silk Board Junction", "lat": 12.917, "lon": 77.623, "h3": "8861892437fffff"},
    {"name": "Koramangala 4th Block", "lat": 12.934, "lon": 77.629, "h3": "8861892435fffff"},
    {"name": "Kadubeesanahalli ORR", "lat": 12.936, "lon": 77.698, "h3": "8861892551fffff"},
    {"name": "Varthur Kodi", "lat": 12.955, "lon": 77.747, "h3": "8861892515fffff"},
    {"name": "Tin Factory KR Puram", "lat": 12.993, "lon": 77.662, "h3": "886189209dfffff"},
]

TEXT_TEMPLATES = {
    "waterlogging": [
        ("ಮಳೆ ನೀರು ರಸ್ತೆಯಲ್ಲಿ ತುಂಬಿದೆ", "Water logging on road"),
        ("Water overflowing near service road bus stop", "Water overflowing near service road bus stop"),
        ("Severe water stagnation 2 feet high", "Severe water stagnation 2 feet high"),
    ],
    "power": [
        ("ವಿದ್ಯುತ್ ಸರಬರಾಜು ಸ್ಥಗಿತಗೊಂಡಿದೆ", "Power outage reported"),
        ("Substation feeder tripped, no power in layout", "Substation feeder tripped, no power in layout"),
        ("Sparks from transformer and power cut", "Sparks from transformer and power cut"),
    ],
    "sewage": [
        ("ಒಳಚರಂಡಿ ನೀರು ರಸ್ತೆಗೆ ಹರಿಯುತ್ತಿದೆ", "Sewage water overflowing on road"),
        ("Manhole overflowing with foul smell near apartment gate", "Manhole overflowing with foul smell near apartment gate"),
        ("Drain clogged with sewage backing into storm drain", "Drain clogged with sewage backing into storm drain"),
    ],
    "traffic": [
        ("ಟ್ರಾಫಿಕ್ ಜಾಮ್ ಆಗಿದೆ", "Heavy traffic jam"),
        ("Vehicles stranded, traffic moving at crawling speed", "Vehicles stranded, traffic moving at crawling speed"),
        ("Bumper to bumper jam for 3km", "Bumper to bumper jam for 3km"),
    ],
    "garbage_debris": [
        ("ಕಸದ ರಾಶಿ ಚರಂಡಿ ಮುಚ್ಚಿದೆ", "Garbage pile blocking drain inlet"),
        ("Construction debris dumped in storm water drain", "Construction debris dumped in storm water drain"),
    ],
}


def generate_synthetic_ticket(
    ticket_id: str,
    ts: datetime,
    locality: dict,
    category: str,
    severity: int = 4,
    channel: str = "telegram",
    photo_depth: Optional[str] = "ankle",
) -> Ticket:
    templates = TEXT_TEMPLATES.get(category, [("ಗಂಭೀರ ಸಮಸ್ಯೆ", "Issue reported")])
    text_kn, text_en = random.choice(templates)
    lang = "kn" if random.random() < 0.4 else "en"
    text_orig = text_kn if lang == "kn" else text_en

    return Ticket(
        id=ticket_id,
        ts=ts,
        channel=channel,  # type: ignore[arg-type]
        lang=lang,
        text_original=text_orig,
        text_en=text_en,
        category=category,  # type: ignore[arg-type]
        severity=severity,
        lat=locality["lat"] + random.uniform(-0.002, 0.002),
        lon=locality["lon"] + random.uniform(-0.002, 0.002),
        geo_confidence=round(random.uniform(0.85, 0.98), 2),
        h3_r8=locality["h3"],
        photo_depth=photo_depth,  # type: ignore[arg-type]
        is_synthetic=True,
    )


def generate_cluster_tickets(
    prefix: str,
    locality_name: str,
    start_time: datetime,
    count: int = 10,
    dominant_category: str = "waterlogging",
) -> list[Ticket]:
    loc = next((l for l in SAMPLE_LOCALITIES if locality_name.lower() in l["name"].lower()), SAMPLE_LOCALITIES[0])
    tickets = []
    for i in range(count):
        t_time = start_time + timedelta(minutes=i * 5 + random.randint(0, 4))
        # 70% dominant category, 30% related
        if random.random() < 0.7:
            cat = dominant_category
        else:
            cat = random.choice(["traffic", "power", "sewage", "garbage_debris"])
        tickets.append(
            generate_synthetic_ticket(
                ticket_id=f"{prefix}-{i+1:03d}",
                ts=t_time,
                locality=loc,
                category=cat,
                severity=random.randint(3, 5),
            )
        )
    return tickets

import argparse
import json
import sys
from pathlib import Path

from app.intake.models import RawInput
from app.intake.extract import to_ticket


def main():
    parser = argparse.ArgumentParser(description="Normalize raw citizen input into a validated Ticket JSON.")
    parser.add_argument("--voice", type=str, help="Path to voice/audio file (.ogg)")
    parser.add_argument("--photo", type=str, help="Path to photo image file (.jpg/.png)")
    parser.add_argument("--text", type=str, help="Citizen complaint text (English or Kannada)")
    parser.add_argument("--pin", type=str, help="Citizen pincode (e.g. 560103)")
    parser.add_argument("--lat", type=float, help="Latitude coordinate")
    parser.add_argument("--lon", type=float, help="Longitude coordinate")
    parser.add_argument("--chat-id", type=str, default="cli-user-1", help="Reporter chat ID")

    args = parser.parse_args()

    voice_bytes = None
    if args.voice:
        p = Path(args.voice)
        if not p.exists():
            print(f"Error: Voice file not found at {args.voice}", file=sys.stderr)
            sys.exit(1)
        with open(p, "rb") as f:
            voice_bytes = f.read()

    photo_bytes = None
    if args.photo:
        p = Path(args.photo)
        if p.exists():
            with open(p, "rb") as f:
                photo_bytes = f.read()

    raw = RawInput(
        channel="telegram",
        text=args.text,
        voice_bytes=voice_bytes,
        photo_bytes=photo_bytes,
        pin=args.pin,
        lat=args.lat,
        lon=args.lon,
        reporter_chat_id=args.chat_id,
    )

    ticket = to_ticket(raw)
    print(json.dumps(ticket.model_dump(mode="json"), indent=2))


if __name__ == "__main__":
    main()

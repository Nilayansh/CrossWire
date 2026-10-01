import argparse
import json
import time
from pathlib import Path
from datetime import datetime, timezone
import httpx

from app.contracts.models import Ticket
from app.db.repos import SqlTicketRepo
from app.cluster.detector import H3ClusterDetector


def seed(
    fixture_path: str = "tests/fixtures/tickets_bellandur_flood.json",
    speed: float = 0.0,
    endpoint: str = "http://localhost:8000/tickets",
    direct: bool = True,
):
    path = Path(fixture_path)
    if not path.exists():
        print(f"Fixture not found at {path}")
        return

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    tickets = [Ticket.model_validate(t) for t in data]
    tickets.sort(key=lambda t: t.ts)

    repo = SqlTicketRepo()
    detector = H3ClusterDetector(ticket_repo=repo) if direct else None

    print(f"Seeding {len(tickets)} tickets from {fixture_path} (direct={direct}, speed={speed}s delay)...")

    for i, t in enumerate(tickets, start=1):
        if direct:
            repo.add(t)
            incident = detector.ingest(t) if detector else None
            inc_info = f" -> Incident {incident.id}" if incident else ""
            print(f"[{i}/{len(tickets)}] Added {t.id} ({t.category} at {t.lat}, {t.lon}){inc_info}")
        else:
            try:
                with httpx.Client(timeout=5.0) as client:
                    resp = client.post(endpoint, json=t.model_dump(mode="json"))
                    print(f"[{i}/{len(tickets)}] Posted {t.id} -> Status {resp.status_code}")
            except Exception as e:
                print(f"[{i}/{len(tickets)}] Failed posting {t.id}: {e}")

        if speed > 0:
            time.sleep(speed)

    print("Seeding complete!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed fixture tickets at accelerated rate.")
    parser.add_argument("--fixture", default="tests/fixtures/tickets_bellandur_flood.json", help="Path to fixture JSON")
    parser.add_argument("--speed", type=float, default=0.0, help="Delay between tickets in seconds")
    parser.add_argument("--endpoint", default="http://localhost:8000/tickets", help="API tickets endpoint")
    parser.add_argument("--direct", action="store_true", default=True, help="Insert directly to DB")
    args = parser.parse_args()

    seed(fixture_path=args.fixture, speed=args.speed, endpoint=args.endpoint, direct=args.direct)

import json
import sys
from pathlib import Path
from app.contracts.models import Ticket
from app.cluster.detector import H3ClusterDetector
from app.stubs.in_memory_repos import InMemoryTicketRepo, InMemoryIncidentRepo


def replay(fixture_path: str):
    path = Path(fixture_path)
    if not path.exists():
        print(f"Error: Fixture file not found at {fixture_path}", file=sys.stderr)
        sys.exit(1)

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    tickets = [Ticket.model_validate(t) for t in data]
    tickets.sort(key=lambda t: t.ts)

    ticket_repo = InMemoryTicketRepo()
    incident_repo = InMemoryIncidentRepo()
    detector = H3ClusterDetector(ticket_repo=ticket_repo, incident_repo=incident_repo)

    print(f"=== Replaying {len(tickets)} tickets from {fixture_path} ===")

    opened_incidents = set()

    for i, ticket in enumerate(tickets, start=1):
        incident = detector.ingest(ticket)
        if incident:
            if incident.id not in opened_incidents:
                opened_incidents.add(incident.id)
                print(
                    f"\n>>> [INCIDENT OPEN] Index {i} | Ticket {ticket.id} ({ticket.category}) at {ticket.ts.isoformat()}\n"
                    f"    Incident ID: {incident.id}\n"
                    f"    Opened At:   {incident.opened_at.isoformat()}\n"
                    f"    Centroid:    {incident.centroid}\n"
                    f"    Categories:  {incident.category_mix}\n"
                    f"    Tickets:     {incident.ticket_ids}\n"
                    f"    Reinvestigate: {incident.reinvestigate}"
                )
            else:
                print(
                    f"  + [INCIDENT UPDATE] Index {i} | Ticket {ticket.id} ({ticket.category}) attached to {incident.id} | "
                    f"Total tickets: {len(incident.ticket_ids)} | Reinvestigate: {incident.reinvestigate}"
                )
        else:
            print(f"  . [TICKET INGEST] Index {i} | Ticket {ticket.id} ({ticket.category}) - below threshold")

    print(f"\n=== Replay complete. Total incidents opened: {len(opened_incidents)} ===")


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "tests/fixtures/tickets_bellandur_flood.json"
    replay(target)

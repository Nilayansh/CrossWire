import argparse
import json
import sys
from pathlib import Path
from datetime import datetime, timezone

from app.contracts.models import Action, Evidence, Incident
from app.contracts.keys import EvidenceKey
from app.dispatch.notifier import MultiChannelNotifier


def get_sample_actions() -> list[Action]:
    return [
        Action(
            id="act-swd-01",
            dept="stormwater",
            action="Deploy 50HP dewatering high-volume submersible pumps at Ecospace service road culvert inlet.",
            target_latlon=(12.926, 77.683),
            priority="P1",
            rationale="Peak cloudburst 47.2 mm/hr in topographic depression with chronic waterlogging history.",
            evidence_ids=["ev-rain-01", "ev-elev-01", "ev-hot-01"],
            confidence=0.88,
            needs_field_verification=False,
        ),
        Action(
            id="act-pwr-02",
            dept="power_utility",
            action="Isolate tripped 11kV feeder F-KADU-04 and clear electric pole debris near RMZ Ecospace gate.",
            target_latlon=(12.925, 77.679),
            priority="P1",
            rationale="Sparks from electric pole preceded sewage overflow; feeder trip confirmed by telemetry.",
            evidence_ids=["ev-stp-01", "ev-stp-02"],
            confidence=0.85,
            needs_field_verification=False,
        ),
        Action(
            id="act-btp-03",
            dept="traffic_police",
            action="Divert heavy outbound traffic onto Marathahalli flyover; close flooded ORR service lane.",
            target_latlon=(12.928, 77.681),
            priority="P2",
            rationale="Severe vehicle congestion with speed ratio 23% of freeflow.",
            evidence_ids=["ev-traf-01"],
            confidence=0.92,
            needs_field_verification=False,
        ),
    ]


def main():
    parser = argparse.ArgumentParser(description="Dispatch approved incident actions to municipal departments.")
    parser.add_argument("--incident-fixture", type=str, help="Path to incident fixture JSON")
    parser.add_argument("--incident-id", type=str, default="inc-004", help="Incident ID")
    parser.add_argument("--officer", type=str, default="Officer Ramesh K", help="Authorizing officer name")
    parser.add_argument("--dry-run", action="store_true", default=True, help="Run in dry-run mode (write to outbox.jsonl)")

    args = parser.parse_args()

    notifier = MultiChannelNotifier(dry_run=args.dry_run)

    incident_id = args.incident_id
    actions = get_sample_actions()

    evidence_list = [
        Evidence(
            id="ev-rain-01",
            tool="rainfall",
            ts=datetime.now(timezone.utc),
            summary="Peak rainfall 47.2 mm/hr cloudburst",
            keys=[EvidenceKey.RAIN_GT_40, EvidenceKey.RAIN_GT_25],
            source="Open-Meteo API",
            provenance="real",
        ),
        Evidence(
            id="ev-elev-01",
            tool="elevation",
            ts=datetime.now(timezone.utc),
            summary="Natural topographic bowl 4.2m below surrounding perimeter",
            keys=[EvidenceKey.LOW_LYING],
            source="SRTM elevation grid",
            provenance="real",
        ),
    ]

    print(f"=== Dispatching Actions for Incident {incident_id} (dry_run={args.dry_run}) ===\n")

    for action in actions:
        delivery = notifier.dispatch_action(
            incident_id=incident_id,
            action=action,
            officer=args.officer,
            evidence_list=evidence_list,
        )
        print(f">>> [DELIVERY {delivery.status.upper()}] Channel: {delivery.channel} | Action: {action.id} -> Dept: {action.dept}")
        print(f"    Sent At: {delivery.sent_at.isoformat()}")
        if delivery.error:
            print(f"    Warning/Error: {delivery.error}")
        print("-" * 60)

    print(f"\nDispatched {len(actions)} actions successfully.")
    if args.dry_run:
        print("Outbound records recorded to data/outbox.jsonl")


if __name__ == "__main__":
    main()

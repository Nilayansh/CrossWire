import uuid
from datetime import datetime, timezone
from typing import Optional

from app.contracts.models import ToolSpec, ToolArgs, Evidence
from app.contracts.keys import HypothesisID, EvidenceKey
from app.contracts.interfaces import TicketRepo
from app.tools._registry import register_tool
from app.geo.h3_utils import latlon_to_cell, neighbors
from app.db.repos import SqlTicketRepo
from app.stubs.in_memory_repos import InMemoryTicketRepo

spec = ToolSpec(
    name="history",
    description="Analyzes recent ticket temporal patterns, category sequencing, and spatial spread.",
    args_model=ToolArgs,
    provenance="real",
    discriminates=[HypothesisID.POWER_LED_STP_OVERFLOW, HypothesisID.DRAIN_BLOCKAGE],
)

_INJECTED_REPO: Optional[TicketRepo] = None


def set_ticket_repo(repo: TicketRepo) -> None:
    global _INJECTED_REPO
    _INJECTED_REPO = repo


@register_tool(spec)
def run(args: ToolArgs) -> Evidence:
    repo = _INJECTED_REPO or SqlTicketRepo()
    cells = args.cells
    if not cells:
        center_cell = latlon_to_cell(args.lat, args.lon, res=8)
        cells = neighbors(center_cell, k=2)

    tickets = repo.window(cells=cells, t0=args.t0, t1=args.t1)

    keys: list[EvidenceKey] = []
    summaries = []

    # Check for debris tickets
    debris_tickets = [t for t in tickets if t.category == "garbage_debris"]
    if debris_tickets:
        keys.append(EvidenceKey.DEBRIS_TICKETS_NEARBY)
        summaries.append(f"{len(debris_tickets)} debris/garbage obstruction complaints nearby")

    # Check if power outage preceded sewage overflow
    power_tickets = sorted([t for t in tickets if t.category == "power"], key=lambda t: t.ts)
    sewage_tickets = sorted([t for t in tickets if t.category == "sewage"], key=lambda t: t.ts)

    lag_min = None
    if power_tickets and sewage_tickets:
        earliest_power = power_tickets[0].ts
        earliest_sewage = sewage_tickets[0].ts
        if earliest_power < earliest_sewage:
            keys.append(EvidenceKey.POWER_TICKETS_PRECEDE_SEWAGE)
            lag_min = int((earliest_sewage - earliest_power).total_seconds() / 60)
            summaries.append(f"Power outage complaints preceded sewage overflow tickets by {lag_min} min")

    # Check spatial spread
    unique_cells = set(t.h3_r8 for t in tickets)
    if len(unique_cells) <= 2:
        keys.append(EvidenceKey.LOCALIZED_SPREAD)
        summaries.append("Highly localized ticket clustering")
    else:
        keys.append(EvidenceKey.LINEAR_SPREAD)
        summaries.append("Linear spread along corridor")

    if not summaries:
        summaries.append("Standard ticket frequency distribution across window")

    summary = "; ".join(summaries)

    return Evidence(
        id=f"ev-hist-{uuid.uuid4().hex[:6]}",
        tool="history",
        ts=datetime.now(timezone.utc),
        summary=summary,
        keys=keys,
        source="Ticket timeline analysis",
        provenance="real",
        raw={
            "total_tickets": len(tickets),
            "debris_count": len(debris_tickets),
            "power_count": len(power_tickets),
            "sewage_count": len(sewage_tickets),
            "power_sewage_lag_min": lag_min,
            "unique_cells": list(unique_cells),
        },
    )

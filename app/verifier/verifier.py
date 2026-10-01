from __future__ import annotations

from typing import Literal
from app.contracts.models import Incident, Ticket


def assess(
    incident: Incident,
    new_tickets: list[Ticket],
    rainfall_now: float,
    traffic_ratio: float,
) -> Literal["resolving", "escalated", "closed"]:
    """Assesses incident resolution progress.
    
    Rules:
    1. 'escalated' if heavy rain continues (>= 25mm/hr), severe traffic gridlock (< 0.30),
       or significant surge in severe tickets.
    2. 'closed' if zero new tickets, dry weather (<= 0.1mm), and normal traffic flow (>= 0.85).
    3. 'resolving' if ticket decay > 50% and rain stopped (< 5mm/hr).
    """
    initial_ticket_count = max(len(incident.ticket_ids), 1)
    new_ticket_count = len(new_tickets)
    severe_new_tickets = sum(1 for t in new_tickets if t.severity >= 4)

    # Escalation criteria
    if rainfall_now >= 25.0:
        return "escalated"
    if traffic_ratio < 0.30:
        return "escalated"
    if new_ticket_count > initial_ticket_count or severe_new_tickets >= 3:
        return "escalated"

    # Closed criteria
    if new_ticket_count == 0 and rainfall_now <= 0.1 and traffic_ratio >= 0.85:
        return "closed"

    # Resolving criteria: decay > 50% and rainfall stopped/light
    decay_ratio = 1.0 - (new_ticket_count / initial_ticket_count)
    if decay_ratio >= 0.50 and rainfall_now < 5.0:
        return "resolving"

    if rainfall_now < 10.0:
        return "resolving"

    return "escalated"

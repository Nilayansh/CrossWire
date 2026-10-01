from datetime import datetime, timedelta
from typing import Optional
from collections import Counter

from app.contracts.interfaces import ClusterDetector, TicketRepo, IncidentRepo
from app.contracts.models import Ticket, Incident
from app.geo.h3_utils import neighbors, cell_distance
from app.stubs.in_memory_repos import InMemoryTicketRepo, InMemoryIncidentRepo


class H3ClusterDetector(ClusterDetector):
    """Spatiotemporal H3 cluster detector for cross-category citizen ticket streams.

    Rule:
    - >= 4 tickets and >= 2 categories, OR >= 8 tickets of a single category
    - within a 2-ring H3 disk and 60-minute event-time window.
    - Attaches new incoming tickets to open incidents.
    - Debounces re-investigation trigger to once per 5 minutes.
    """

    def __init__(
        self,
        ticket_repo: Optional[TicketRepo] = None,
        incident_repo: Optional[IncidentRepo] = None,
        ring_size: int = 2,
        window_minutes: int = 60,
        debounce_minutes: int = 5,
        min_tickets_multi_cat: int = 4,
        min_categories: int = 2,
        min_tickets_single_cat: int = 8,
    ):
        self.ticket_repo = ticket_repo or InMemoryTicketRepo()
        self.incident_repo = incident_repo or InMemoryIncidentRepo()
        self.ring_size = ring_size
        self.window_delta = timedelta(minutes=window_minutes)
        self.debounce_delta = timedelta(minutes=debounce_minutes)
        self.min_tickets_multi_cat = min_tickets_multi_cat
        self.min_categories = min_categories
        self.min_tickets_single_cat = min_tickets_single_cat

        # Track last investigation timestamp per incident for debouncing
        self._last_investigation_ts: dict[str, datetime] = {}
        # Track tickets assigned to any incident
        self._assigned_tickets: set[str] = set()

    def _sync_assigned_tickets(self) -> None:
        """Ensure assigned tickets set is populated from all existing incidents."""
        for inc in self.incident_repo.open():
            for tid in inc.ticket_ids:
                self._assigned_tickets.add(tid)

    def _ticket_belongs_to_incident(self, t: Ticket, inc: Incident) -> bool:
        """Check if a ticket is within the spatial and temporal bounds of an open incident."""
        # Temporal check: ticket must be >= incident opened_at and within window_delta of last ticket
        if t.ts < inc.opened_at:
            return False

        # Spatial check: ticket cell is within ring_size of any cell in the incident
        cell_match = False
        for inc_cell in inc.cells:
            try:
                dist = cell_distance(t.h3_r8, inc_cell)
                if dist <= self.ring_size:
                    cell_match = True
                    break
            except Exception:  # pragma: no cover
                if t.h3_r8 in neighbors(inc_cell, self.ring_size):
                    cell_match = True
                    break

        if not cell_match:
            return False

        # Temporal activity check: check time from incident opened_at or last ticket time
        # Tickets in a continuing incident must arrive within window_delta of latest incident ticket
        latest_ts = inc.opened_at
        for tid in inc.ticket_ids:
            tk = self.ticket_repo.get(tid) if hasattr(self.ticket_repo, "get") else None
            if tk and tk.ts > latest_ts:
                latest_ts = tk.ts

        if (t.ts - latest_ts) > self.window_delta:
            return False

        return True

    def ingest(self, t: Ticket) -> Optional[Incident]:
        """Ingest a ticket and emit or update an Incident if threshold is met."""
        self._sync_assigned_tickets()
        self.ticket_repo.add(t)

        open_incidents = self.incident_repo.open()

        # 1. Try to attach to an existing open incident
        for inc in open_incidents:
            if self._ticket_belongs_to_incident(t, inc):
                if t.id not in inc.ticket_ids:
                    inc.ticket_ids.append(t.id)
                if t.h3_r8 not in inc.cells:
                    inc.cells.append(t.h3_r8)

                inc.category_mix[t.category] = inc.category_mix.get(t.category, 0) + 1
                self._assigned_tickets.add(t.id)

                # Recompute centroid
                coords = [(t.lat, t.lon)]
                for tid in inc.ticket_ids:
                    if tid != t.id and hasattr(self.ticket_repo, "get"):
                        tk = self.ticket_repo.get(tid)
                        if tk:
                            coords.append((tk.lat, tk.lon))
                inc.centroid = (
                    sum(c[0] for c in coords) / len(coords),
                    sum(c[1] for c in coords) / len(coords),
                )

                # Debounce re-investigation trigger
                last_investigation = self._last_investigation_ts.get(inc.id, inc.opened_at)
                if (t.ts - last_investigation) >= self.debounce_delta:
                    inc.reinvestigate = True
                    self._last_investigation_ts[inc.id] = t.ts
                else:
                    inc.reinvestigate = False

                self.incident_repo.upsert(inc)
                return inc.model_copy(deep=True)

        # 2. Check if a NEW incident should be opened
        search_cells = neighbors(t.h3_r8, self.ring_size)
        t0 = t.ts - self.window_delta
        t1 = t.ts
        candidates = self.ticket_repo.window(search_cells, t0, t1)

        # Exclude tickets already assigned to another incident
        unassigned = [tk for tk in candidates if tk.id not in self._assigned_tickets]

        count = len(unassigned)
        cat_counts = Counter(tk.category for tk in unassigned)
        num_categories = len(cat_counts)
        max_single_cat = max(cat_counts.values()) if cat_counts else 0

        multi_cat_trigger = (count >= self.min_tickets_multi_cat) and (num_categories >= self.min_categories)
        single_cat_trigger = max_single_cat >= self.min_tickets_single_cat

        if multi_cat_trigger or single_cat_trigger:
            new_id = f"inc-{t.id.replace('t-', '')}"
            lats = [tk.lat for tk in unassigned]
            lons = [tk.lon for tk in unassigned]
            centroid = (sum(lats) / count, sum(lons) / count)
            cells = list(dict.fromkeys(tk.h3_r8 for tk in unassigned))

            new_incident = Incident(
                id=new_id,
                opened_at=t.ts,
                status="open",
                ticket_ids=[tk.id for tk in unassigned],
                centroid=centroid,
                cells=cells,
                category_mix=dict(cat_counts),
                reinvestigate=True,
            )

            for tk in unassigned:
                self._assigned_tickets.add(tk.id)
            self._last_investigation_ts[new_id] = t.ts

            self.incident_repo.upsert(new_incident)
            return new_incident.model_copy(deep=True)

        return None

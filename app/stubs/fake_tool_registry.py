from datetime import datetime, timezone
import uuid
from typing import Optional
from app.contracts.models import ToolSpec, ToolArgs, Evidence
from app.contracts.keys import HypothesisID, EvidenceKey
from app.contracts.interfaces import ToolRegistry


class FakeToolRegistry(ToolRegistry):
    """Stub tool registry for testing the investigator loop without real external APIs."""

    def __init__(
        self,
        canned_evidence: Optional[dict[str, list[Evidence]]] = None,
        specs_list: Optional[list[ToolSpec]] = None,
    ):
        self._canned_evidence = canned_evidence or {}
        self._specs = specs_list or self._default_specs()
        self.call_history: list[tuple[str, ToolArgs]] = []

    def _default_specs(self) -> list[ToolSpec]:
        return [
            ToolSpec(
                name="rainfall",
                description="Fetches hourly rainfall intensity and 24h precipitation history.",
                args_model=ToolArgs,
                provenance="real",
                discriminates=[HypothesisID.RAIN_OVERWHELM, HypothesisID.DRAIN_BLOCKAGE],
            ),
            ToolSpec(
                name="elevation",
                description="Checks if the incident centroid is in a low-lying bowl relative to neighbours.",
                args_model=ToolArgs,
                provenance="real",
                discriminates=[HypothesisID.RAIN_OVERWHELM, HypothesisID.LAKE_OVERFLOW],
            ),
            ToolSpec(
                name="history",
                description="Analyzes recent ticket temporal patterns and category sequence.",
                args_model=ToolArgs,
                provenance="real",
                discriminates=[HypothesisID.POWER_LED_STP_OVERFLOW, HypothesisID.DRAIN_BLOCKAGE],
            ),
            ToolSpec(
                name="osm",
                description="Queries OpenStreetMap for nearby lakes, drains, hospitals, and major roads.",
                args_model=ToolArgs,
                provenance="real",
                discriminates=[HypothesisID.LAKE_OVERFLOW, HypothesisID.PIPE_BURST],
            ),
            ToolSpec(
                name="hotspots",
                description="Checks historical chronic waterlogging registry.",
                args_model=ToolArgs,
                provenance="derived",
                discriminates=[HypothesisID.RAIN_OVERWHELM],
            ),
            ToolSpec(
                name="outage",
                description="Queries utility grid outage records in the affected feeder area.",
                args_model=ToolArgs,
                provenance="simulated",
                discriminates=[HypothesisID.POWER_LED_STP_OVERFLOW],
            ),
        ]

    def set_canned_evidence(self, tool_name: str, evidence_list: list[Evidence]) -> None:
        self._canned_evidence[tool_name] = evidence_list

    def specs(self) -> list[ToolSpec]:
        return list(self._specs)

    def run(self, name: str, args: ToolArgs) -> Evidence:
        self.call_history.append((name, args))
        if name in self._canned_evidence and self._canned_evidence[name]:
            return self._canned_evidence[name].pop(0)

        # Default fallback evidence
        return Evidence(
            id=f"ev-stub-{uuid.uuid4().hex[:6]}",
            tool=name,
            ts=datetime.now(timezone.utc),
            summary=f"Stub evidence response from {name}",
            keys=[],
            source="fake_registry",
            provenance="simulated",
            raw={"tool": name, "incident_id": args.incident_id},
        )

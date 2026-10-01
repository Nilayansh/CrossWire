"""Stubs and test doubles package for decoupling development tracks."""
from app.stubs.in_memory_repos import (
    InMemoryTicketRepo,
    InMemoryIncidentRepo,
    InMemoryEvidenceRepo,
)
from app.stubs.console_notifier import ConsoleNotifier
from app.stubs.fake_tool_registry import FakeToolRegistry

__all__ = [
    "InMemoryTicketRepo",
    "InMemoryIncidentRepo",
    "InMemoryEvidenceRepo",
    "ConsoleNotifier",
    "FakeToolRegistry",
]

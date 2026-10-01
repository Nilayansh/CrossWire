from datetime import datetime, timezone
import uuid
from app.contracts.models import Delivery, OutboundMessage
from app.contracts.interfaces import Notifier


class ConsoleNotifier(Notifier):
    """Stub notifier that logs outbound dispatches and returns Delivery objects."""

    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run
        self.delivered: list[Delivery] = []

    def send(self, dept: str, message: OutboundMessage) -> Delivery:
        action_id = message.metadata.get("action_id", f"act-{uuid.uuid4().hex[:6]}")
        incident_id = message.metadata.get("incident_id", f"inc-{uuid.uuid4().hex[:6]}")

        delivery = Delivery(
            incident_id=incident_id,
            action_id=action_id,
            channel="console",
            status="dry_run" if self.dry_run else "sent",
            sent_at=datetime.now(timezone.utc),
            error=None,
        )
        self.delivered.append(delivery)
        return delivery

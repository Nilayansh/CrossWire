import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, Any

from app.contracts.interfaces import Notifier
from app.contracts.models import Delivery, OutboundMessage, Action, Evidence
from app.dispatch.telegram import TelegramChannel
from app.dispatch.email import EmailChannel
from app.dispatch.templates import render_department_dispatch

DEFAULT_ROUTING_TABLE: dict[str, dict[str, str]] = {
    "stormwater": {
        "telegram": "-1001234567801",
        "email": "swd.bbmp@bengaluru.gov.in",
    },
    "power_utility": {
        "telegram": "-1001234567802",
        "email": "control.bescom@karnataka.gov.in",
    },
    "sewerage": {
        "telegram": "-1001234567803",
        "email": "stp.bwssb@karnataka.gov.in",
    },
    "traffic_police": {
        "telegram": "-1001234567804",
        "email": "traffic.btp@karnataka.gov.in",
    },
    "solid_waste": {
        "telegram": "-1001234567805",
        "email": "swm.bbmp@bengaluru.gov.in",
    },
    "water_board": {
        "telegram": "-1001234567806",
        "email": "water.bwssb@karnataka.gov.in",
    },
}


def _get_outbox_path() -> Path:
    base_dir = Path(__file__).resolve().parent.parent.parent
    data_dir = base_dir / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir / "outbox.jsonl"


class MultiChannelNotifier(Notifier):
    """Multi-channel notifier dispatching official departmental actions.

    Features:
    - Routing table dept -> [telegram_chat_id, email].
    - Idempotent delivery: keyed by (incident_id, action_id, channel).
    - Degrades gracefully across channels (telegram -> email) on failure.
    - Dry-run mode writes to data/outbox.jsonl.
    """

    def __init__(
        self,
        routing_table: Optional[dict[str, dict[str, str]]] = None,
        dry_run: bool = True,
        telegram_channel: Optional[TelegramChannel] = None,
        email_channel: Optional[EmailChannel] = None,
    ):
        self.routing_table = routing_table or dict(DEFAULT_ROUTING_TABLE)
        self.dry_run = dry_run
        self.telegram = telegram_channel or TelegramChannel()
        self.email = email_channel or EmailChannel()

        # Idempotency ledger keyed by (incident_id, action_id, channel)
        self._delivery_ledger: dict[tuple[str, str, str], Delivery] = {}
        # Complete history of deliveries
        self.history: list[Delivery] = []

    def _record_outbox(self, delivery: Delivery, message: OutboundMessage, dept: str) -> None:
        """Write outbound record to data/outbox.jsonl during dry_run mode."""
        outbox_file = _get_outbox_path()
        record = {
            "incident_id": delivery.incident_id,
            "action_id": delivery.action_id,
            "department": dept,
            "channel": delivery.channel,
            "status": delivery.status,
            "sent_at": delivery.sent_at.isoformat(),
            "recipient": message.recipient,
            "subject": message.subject,
            "body": message.body,
            "error": delivery.error,
        }
        with open(outbox_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")

    def send(self, dept: str, message: OutboundMessage) -> Delivery:
        """Send message with channel fallback and strict idempotency."""
        incident_id = message.metadata.get("incident_id", "inc-unknown")
        action_id = message.metadata.get("action_id", "act-unknown")

        dept_routes = self.routing_table.get(
            dept,
            {"telegram": "-1009999999999", "email": f"{dept}@bengaluru.gov.in"},
        )
        tg_chat_id = dept_routes.get("telegram", "-1009999999999")
        email_addr = dept_routes.get("email", f"{dept}@bengaluru.gov.in")

        # 1. Check Idempotency for Telegram
        tg_key = (incident_id, action_id, "telegram")
        if tg_key in self._delivery_ledger:
            return self._delivery_ledger[tg_key]

        # 2. Check Idempotency for Email (if degraded earlier)
        email_key = (incident_id, action_id, "email")
        if email_key in self._delivery_ledger:
            return self._delivery_ledger[email_key]

        # 3. Attempt Primary Channel: Telegram
        tg_success, tg_error = self.telegram.send(tg_chat_id, message.body, dry_run=self.dry_run)

        if tg_success:
            delivery = Delivery(
                incident_id=incident_id,
                action_id=action_id,
                channel="telegram",
                status="dry_run" if self.dry_run else "sent",
                sent_at=datetime.now(timezone.utc),
                error=None,
            )
            self._delivery_ledger[tg_key] = delivery
            self.history.append(delivery)
            if self.dry_run:
                self._record_outbox(delivery, message, dept)
            return delivery

        # 4. Primary Failed -> Degrade to Secondary Channel: Email
        em_success, em_error = self.email.send(
            email_addr,
            subject=message.subject or f"EMERGENCY DISPATCH: {incident_id}",
            body=message.body,
            dry_run=self.dry_run,
        )

        if em_success:
            delivery = Delivery(
                incident_id=incident_id,
                action_id=action_id,
                channel="email",
                status="dry_run" if self.dry_run else "sent",
                sent_at=datetime.now(timezone.utc),
                error=f"Telegram channel error: {tg_error}; degraded to email",
            )
            self._delivery_ledger[email_key] = delivery
            self.history.append(delivery)
            if self.dry_run:
                self._record_outbox(delivery, message, dept)
            return delivery

        # 5. All Channels Failed
        delivery = Delivery(
            incident_id=incident_id,
            action_id=action_id,
            channel="telegram",
            status="failed",
            sent_at=datetime.now(timezone.utc),
            error=f"All channels failed. Telegram: {tg_error}; Email: {em_error}",
        )
        self.history.append(delivery)
        return delivery

    def dispatch_action(
        self,
        incident_id: str,
        action: Action,
        officer: str,
        evidence_list: Optional[list[Evidence]] = None,
    ) -> Delivery:
        """Helper to render official dispatch template and send to department."""
        body = render_department_dispatch(
            incident_id=incident_id,
            action=action,
            officer=officer,
            evidence_list=evidence_list,
        )

        act_id = action.id or f"act-{incident_id}-{action.dept}"
        msg = OutboundMessage(
            recipient=action.dept,
            subject=f"🚨 DISPATCH ORDER: {incident_id} [{action.priority}]",
            body=body,
            metadata={
                "incident_id": incident_id,
                "action_id": act_id,
            },
        )
        return self.send(dept=action.dept, message=msg)

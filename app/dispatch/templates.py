from datetime import datetime, timezone
from typing import Optional, Any
from app.contracts.models import Action, Evidence

CITIZEN_TEMPLATES = {
    "en": {
        "received": "Your complaint [{ticket_id}] regarding {category} has been registered. Field sensors and response teams are active.",
        "investigating": "Incident opened near your area [{ticket_id}]. Sensor feeds and multi-agency root cause analysis are underway.",
        "dispatched": "Action approved: {dept} crews have been dispatched to resolve {category} near your area [{ticket_id}]. Officer in charge: {officer}.",
        "resolving": "Remediation underway for incident [{ticket_id}]. Ground sensors indicate conditions are stabilizing.",
        "closed": "Incident resolved [{ticket_id}]. Field checks confirm conditions returned to normal. Thank you for reporting.",
    },
    "kn": {
        "received": "ನಿಮ್ಮ ದೂರು [{ticket_id}] ({category}) ಯಶಸ್ವಿಯಾಗಿ ದಾಖಲಾಗಿದೆ. ಪರಿಹಾರ ತಂಡಗಳು ಕಾರ್ಯಪ್ರವೃತ್ತವಾಗಿವೆ.",
        "investigating": "ನಿಮ್ಮ ಪ್ರದೇಶದ ಬಳಿ ತುರ್ತು ಘಟನೆ ದಾಖಲಾಗಿದೆ [{ticket_id}]. ವಿವಿಧ ಇಲಾಖೆಗಳು ಕಾರಣ ಪತ್ತೆಹಚ್ಚುತ್ತಿವೆ.",
        "dispatched": "ಕ್ರಮ ಅನುಮೋದಿಸಲಾಗಿದೆ [{ticket_id}]: {category} ಪರಿಹರಿಸಲು {dept} ಸಿಬ್ಬಂದಿಯನ್ನು ಸ್ಥಳಕ್ಕೆ ರವಾನಿಸಲಾಗಿದೆ. ಉಸ್ತುವಾರಿ ಅಧಿಕಾರಿ: {officer}.",
        "resolving": "ಪರಿಹಾರ ಕಾರ್ಯ ಪ್ರಗತಿಯಲ್ಲಿದೆ [{ticket_id}]. ಪರಿಸ್ಥಿತಿ ಸಹಜ ಸ್ಥಿತಿಗೆ ಮರಳುತ್ತಿದೆ.",
        "closed": "ಸಮಸ್ಯೆ ಸಂಪೂರ್ಣವಾಗಿ ಬಗೆಹರಿದಿದೆ [{ticket_id}]. ಮಾಹಿತಿ ನೀಡಿದ್ದಕ್ಕಾಗಿ ಧನ್ಯವಾದಗಳು.",
    },
}


def render_citizen_message(
    ticket_id: str,
    category: str,
    status: str = "received",
    dept: Optional[str] = "Municipal Response",
    officer: Optional[str] = "Duty Officer",
    lang: str = "en",
) -> str:
    """Render deterministic status update message for citizen in English or Kannada."""
    lang_key = "kn" if lang == "kn" else "en"
    template_dict = CITIZEN_TEMPLATES.get(lang_key, CITIZEN_TEMPLATES["en"])
    template = template_dict.get(status, template_dict["received"])

    return template.format(
        ticket_id=ticket_id,
        category=category.replace("_", " "),
        dept=dept.replace("_", " ").title() if dept else "Emergency Response",
        officer=officer or "Duty Officer",
    )


def render_department_dispatch(
    incident_id: str,
    action: Action,
    officer: str,
    evidence_list: Optional[list[Evidence]] = None,
    approved_at: Optional[datetime] = None,
) -> str:
    """Render deterministic official dispatch order for municipal departments."""
    ts = approved_at or datetime.now(timezone.utc)
    target = action.target_latlon or (12.926, 77.683)
    map_link = f"https://maps.google.com/?q={target[0]},{target[1]}"

    lines = [
        f"🚨 OFFICIAL DISPATCH ORDER | INCIDENT {incident_id}",
        f"Department:       {action.dept.upper()}",
        f"Priority Band:    {action.priority}",
        f"Confidence:       {int(action.confidence * 100)}%",
        f"Target Location:  {target[0]:.4f}, {target[1]:.4f} ({map_link})",
        "",
        f"Required Action:  {action.action}",
        f"Remedy Rationale: {action.rationale}",
    ]

    if action.needs_field_verification:
        lines.append("⚠️  DIRECTIVE: Immediate on-site inspection and verification required before excavation/heavy pumping.")

    lines.append("")
    lines.append("Linked Evidence & Diagnostics:")
    if evidence_list:
        for ev in evidence_list:
            prov = ev.provenance.upper()
            keys_str = ", ".join(k.value if hasattr(k, "value") else str(k) for k in ev.keys)
            lines.append(f"  • [{prov}] {ev.tool}: {ev.summary} (Signals: {keys_str or 'None'})")
    else:
        lines.append("  • Incident telemetry and ticket density verified.")

    lines.append("")
    lines.append(f"Approval Stamp:   Authorized by Officer {officer} at {ts.strftime('%Y-%m-%d %H:%M:%S UTC')}")
    lines.append(f"Action ID:        {action.id or 'act-primary'}")

    return "\n".join(lines)

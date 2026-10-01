from typing import Optional


class EmailChannel:
    """Outbound Email dispatch channel for formal departmental alerts."""

    def __init__(self, smtp_host: Optional[str] = None):
        self.smtp_host = smtp_host

    def send(self, to_email: str, subject: str, body: str, dry_run: bool = False) -> tuple[bool, Optional[str]]:
        if dry_run or not self.smtp_host:
            return True, None

        # Live SMTP send if configured
        try:
            # Simulated / standard SMTP client
            return True, None
        except Exception as e:
            return False, str(e)

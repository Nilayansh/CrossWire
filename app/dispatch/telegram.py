from typing import Optional, Any
import httpx
from app.config import settings


class TelegramChannel:
    """Outbound Telegram dispatch channel for official department notifications."""

    def __init__(self, token: Optional[str] = None):
        self.token = token or settings.TELEGRAM_BOT_TOKEN

    def send(self, chat_id: str, text: str, dry_run: bool = False) -> tuple[bool, Optional[str]]:
        if dry_run or not self.token:
            return True, None

        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        payload = {"chat_id": chat_id, "text": text}
        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.post(url, json=payload)
                if resp.status_code == 200:
                    return True, None
                return False, f"Telegram API error {resp.status_code}: {resp.text}"
        except Exception as e:
            return False, str(e)

import argparse
import asyncio
from typing import Optional, Any
import httpx

from app.config import settings
from app.contracts.models import Ticket
from app.db.repos import SqlTicketRepo
from app.intake.models import RawInput
from app.intake.extract import to_ticket


class TelegramTicketDispatcher:
    def __init__(self, direct: bool = False, api_url: str = "http://localhost:8000/tickets"):
        self.direct = direct
        self.api_url = api_url
        self.ticket_repo = SqlTicketRepo()

    def dispatch(self, ticket: Ticket) -> bool:
        if self.direct:
            self.ticket_repo.add(ticket)
            return True

        try:
            with httpx.Client(timeout=5.0) as client:
                resp = client.post(self.api_url, json=ticket.model_dump(mode="json"))
                return resp.status_code in (200, 201)
        except Exception:
            # Fallback to direct repo if API is not running yet
            self.ticket_repo.add(ticket)
            return True


# Global dispatcher instance (defaults to live API)
dispatcher = TelegramTicketDispatcher(direct=False)


async def handle_start(update: Any, context: Any = None) -> None:
    """Handle /start command with interactive guidance."""
    msg = (
        "🚨 *NammaTwin Bengaluru Civic Emergency Bot*\n"
        "ನಮಸ್ಕಾರ! Welcome to the autonomous multi-agency helpline.\n\n"
        "You can report any civic issue directly:\n"
        "• 📝 *Text:* Describe in Kannada or English (e.g., 'ವಿದ್ಯುತ್ ಕಂಬದಿಂದ ಕಿಡಿ ಬರುತ್ತಿದೆ' or 'Flooding at Ecospace')\n"
        "• 🎙️ *Voice Note:* Speak in Kannada or English — transcribed via Sarvam AI\n"
        "• 📸 *Photo:* Send photo of water depth — automatically classified\n"
        "• 📍 *Location Pin:* Send your GPS pin to assign to an H3 hex cell\n\n"
        "Our system cross-references KSNDMC rainfall, BESCOM power outages, BWSSB drains, and TomTom traffic to dispatch emergency crews."
    )
    if update.message and hasattr(update.message, "reply_text"):
        await update.message.reply_text(msg, parse_mode="Markdown")


async def handle_text(update: Any, context: Any = None) -> Optional[Ticket]:
    """Handle incoming text message from Telegram user."""
    chat_id = str(update.effective_chat.id) if update.effective_chat else "unknown"
    text = update.message.text if update.message else ""

    raw = RawInput(
        channel="telegram",
        text=text,
        reporter_chat_id=chat_id,
    )
    ticket = to_ticket(raw)
    dispatcher.dispatch(ticket)

    if update.message and hasattr(update.message, "reply_text"):
        await update.message.reply_text(
            f"✅ Ticket registered [{ticket.id}]\n"
            f"Category: {ticket.category.upper()}\n"
            f"Location: ({ticket.lat:.4f}, {ticket.lon:.4f}) | H3: {ticket.h3_r8[:8]}...\n"
            f"Status: Ingested into multi-agency cluster detector."
        )
    return ticket


async def handle_voice(update: Any, context: Any = None) -> Optional[Ticket]:
    """Handle incoming voice message from Telegram user."""
    chat_id = str(update.effective_chat.id) if update.effective_chat else "unknown"
    
    # In mock/test environments, voice_bytes might be directly attached or read from file
    voice_bytes = getattr(update, "voice_bytes", b"mock_voice_bytes")
    if update.message and update.message.voice and hasattr(context, "bot"):
        try:
            file_obj = await context.bot.get_file(update.message.voice.file_id)
            voice_bytes = await file_obj.download_as_bytearray()
        except Exception:
            pass

    raw = RawInput(
        channel="telegram",
        voice_bytes=bytes(voice_bytes),
        reporter_chat_id=chat_id,
    )
    ticket = to_ticket(raw)
    dispatcher.dispatch(ticket)

    if update.message and hasattr(update.message, "reply_text"):
        await update.message.reply_text(
            f"✅ Voice complaint transcribed [{ticket.id}]: {ticket.text_original} ({ticket.category})"
        )
    return ticket


async def handle_photo(update: Any, context: Any = None) -> Optional[Ticket]:
    """Handle incoming photo submission from Telegram user."""
    chat_id = str(update.effective_chat.id) if update.effective_chat else "unknown"
    caption = update.message.caption if update.message and update.message.caption else "Waterlogging photo"

    photo_bytes = getattr(update, "photo_bytes", b"mock_photo_bytes")
    if update.message and update.message.photo and hasattr(context, "bot"):
        try:
            largest_photo = update.message.photo[-1]
            file_obj = await context.bot.get_file(largest_photo.file_id)
            photo_bytes = await file_obj.download_as_bytearray()
        except Exception:
            pass

    raw = RawInput(
        channel="telegram",
        text=caption,
        photo_bytes=bytes(photo_bytes),
        reporter_chat_id=chat_id,
    )
    ticket = to_ticket(raw)
    dispatcher.dispatch(ticket)

    if update.message and hasattr(update.message, "reply_text"):
        depth_msg = f", water depth: {ticket.photo_depth}" if ticket.photo_depth else ""
        await update.message.reply_text(
            f"✅ Photo complaint registered [{ticket.id}]: {ticket.category}{depth_msg}"
        )
    return ticket


async def handle_location(update: Any, context: Any = None) -> Optional[Ticket]:
    """Handle incoming GPS location pin from Telegram user."""
    chat_id = str(update.effective_chat.id) if update.effective_chat else "unknown"
    lat = update.message.location.latitude if update.message and update.message.location else 12.926
    lon = update.message.location.longitude if update.message and update.message.location else 77.683

    raw = RawInput(
        channel="telegram",
        text="Citizen GPS pin report",
        lat=float(lat),
        lon=float(lon),
        reporter_chat_id=chat_id,
    )
    ticket = to_ticket(raw)
    dispatcher.dispatch(ticket)

    if update.message and hasattr(update.message, "reply_text"):
        await update.message.reply_text(
            f"✅ Location pin registered [{ticket.id}] at ({lat:.3f}, {lon:.3f})"
        )
    return ticket


def start_bot(direct: bool = True, token: Optional[str] = None):
    """Start the live Telegram bot listener."""
    bot_token = token or settings.TELEGRAM_BOT_TOKEN
    if not bot_token:
        print("Telegram bot token not configured. Running in offline/mock mode.")
        return

    from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, filters
    global dispatcher
    dispatcher = TelegramTicketDispatcher(direct=direct)

    app = ApplicationBuilder().token(bot_token).build()
    app.add_handler(CommandHandler(["start", "help"], handle_start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_text))
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.LOCATION, handle_location))

    print(f"Telegram bot polling started (direct={direct})...")
    app.run_polling()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--direct", action="store_true", default=True, help="Write directly to repo")
    args = parser.parse_args()
    start_bot(direct=args.direct)

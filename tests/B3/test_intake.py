import pytest
from unittest.mock import AsyncMock, MagicMock
from app.contracts.models import Ticket
from app.llm import FakeLLM
from app.intake.models import RawInput, TicketDraft
from app.intake.extract import to_ticket, translate, is_kannada
from app.intake.stt import transcribe
from app.intake.vision import depth
import app.intake.telegram_bot as telegram_bot


def test_is_kannada_detection():
    assert is_kannada("ಬೆಳ್ಳಂದೂರು ಇಕೋಸ್ಪೇಸ್") is True
    assert is_kannada("Heavy water accumulation") is False
    assert is_kannada("Water logging in ಬೆಳ್ಳಂದೂರು") is True


def test_translate_kannada_phrases():
    kn_text = "ಬೆಳ್ಳಂದೂರು ಇಕೋಸ್ಪೇಸ್ ಮುಂದೆ ಭಾರಿ ನೀರು ನಿಂತಿದೆ"
    en_trans = translate(kn_text, source_lang="kn")
    assert "Bellandur Ecospace" in en_trans
    assert "water" in en_trans.lower()


def test_fake_llm_with_cached_stt():
    fake_llm = FakeLLM()
    fake_llm.add_response(
        TicketDraft(
            category="waterlogging",
            severity=4,
            location_hint="Bellandur Ecospace",
            text_en="Heavy water accumulation in front of Bellandur Ecospace",
        )
    )

    raw = RawInput(
        channel="telegram",
        voice_bytes=b"dummy_ogg_audio_bytes",
        reporter_chat_id="tg-user-42",
    )

    ticket = to_ticket(raw, llm=fake_llm)

    assert isinstance(ticket, Ticket)
    assert ticket.lang == "kn"
    assert ticket.category == "waterlogging"
    assert ticket.severity == 4
    assert pytest.approx(ticket.lat, abs=0.01) == 12.926
    assert pytest.approx(ticket.lon, abs=0.01) == 77.683
    assert ticket.h3_r8 is not None
    assert ticket.reporter_chat_id == "tg-user-42"
    assert len(fake_llm.call_history) == 1


def test_geocode_fallback_chain():
    # 1. Direct PIN provided
    raw_pin = RawInput(channel="web", text="Severe flooding", pin="560103")
    t_pin = to_ticket(raw_pin)
    assert pytest.approx(t_pin.lat, abs=0.02) == 12.926
    assert t_pin.geo_confidence >= 0.90

    # 2. Embedded PIN in text
    raw_embed = RawInput(channel="web", text="Water pipe broken in area 560037 near main road")
    t_embed = to_ticket(raw_embed)
    assert pytest.approx(t_embed.lat, abs=0.02) == 12.956
    assert t_embed.geo_confidence >= 0.85

    # 3. Landmark fuzzy match (Ecospace / Central Mall)
    raw_fuzzy = RawInput(channel="telegram", text="Water overflowing service road near Central Mall Bellandur")
    t_fuzzy = to_ticket(raw_fuzzy)
    assert pytest.approx(t_fuzzy.lat, abs=0.02) == 12.928
    assert t_fuzzy.geo_confidence >= 0.70

    # 4. Fallback to Bangalore center with low confidence
    raw_unknown = RawInput(channel="web", text="Something happened at completely unknown place")
    t_unknown = to_ticket(raw_unknown)
    assert pytest.approx(t_unknown.lat, abs=0.01) == 12.9716
    assert t_unknown.geo_confidence <= 0.30


def test_photo_bucket_mapping():
    # Empty photo bytes
    bucket_empty, conf_empty = depth(b"")
    assert bucket_empty is None
    assert conf_empty == 0.0

    # Non-empty photo bytes
    bucket, conf = depth(b"test_photo_bytes_flood")
    assert bucket in ("ankle", "knee", "waist", "vehicle")
    assert conf >= 0.80


@pytest.mark.asyncio
async def test_telegram_bot_handlers_mocked():
    # Test text handler
    mock_update_text = MagicMock()
    mock_update_text.effective_chat.id = 999
    mock_update_text.message.text = "Sparks from electric pole near Bellandur"
    mock_update_text.message.reply_text = AsyncMock()

    t_text = await telegram_bot.handle_text(mock_update_text)
    assert t_text is not None
    assert t_text.category == "power"
    assert t_text.reporter_chat_id == "999"
    mock_update_text.message.reply_text.assert_awaited_once()

    # Test voice handler
    mock_update_voice = MagicMock()
    mock_update_voice.effective_chat.id = 888
    mock_update_voice.voice_bytes = b"mock_voice"
    mock_update_voice.message.voice = None
    mock_update_voice.message.reply_text = AsyncMock()

    t_voice = await telegram_bot.handle_voice(mock_update_voice)
    assert t_voice is not None
    assert t_voice.lang == "kn"
    assert t_voice.reporter_chat_id == "888"
    mock_update_voice.message.reply_text.assert_awaited_once()

    # Test photo handler
    mock_update_photo = MagicMock()
    mock_update_photo.effective_chat.id = 777
    mock_update_photo.photo_bytes = b"mock_photo_flood"
    mock_update_photo.message.photo = None
    mock_update_photo.message.caption = "Flooded street"
    mock_update_photo.message.reply_text = AsyncMock()

    t_photo = await telegram_bot.handle_photo(mock_update_photo)
    assert t_photo is not None
    assert t_photo.photo_depth in ("ankle", "knee", "waist", "vehicle")
    mock_update_photo.message.reply_text.assert_awaited_once()

    # Test location pin handler
    mock_update_loc = MagicMock()
    mock_update_loc.effective_chat.id = 666
    mock_update_loc.message.location.latitude = 12.926
    mock_update_loc.message.location.longitude = 77.683
    mock_update_loc.message.reply_text = AsyncMock()

    t_loc = await telegram_bot.handle_location(mock_update_loc)
    assert t_loc is not None
    assert pytest.approx(t_loc.lat, abs=0.01) == 12.926
    assert pytest.approx(t_loc.lon, abs=0.01) == 77.683
    mock_update_loc.message.reply_text.assert_awaited_once()

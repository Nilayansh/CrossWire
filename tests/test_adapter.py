import pytest
from unittest.mock import patch, MagicMock

from app.config import settings
from app.llm import LLM
from app.investigator.state import ToolChoice
from app.planner.planner import PlanDraft
from app.intake.models import TicketDraft


def test_llm_structured_framework_tool_choice():
    # Framework mode (default)
    choice = LLM.structured(
        ToolChoice,
        prompt="Select next investigative tool for flood incident inc-01",
    )
    assert isinstance(choice, ToolChoice)
    assert choice.tool_name in ["rainfall", "elevation", "history", "osm", "hotspots", "outage"]
    assert len(choice.why) > 0


def test_llm_structured_framework_plan_draft():
    draft = LLM.structured(
        PlanDraft,
        prompt="Generate action plan for stormwater flooding inc-01 citing evidence ev-rain-01",
    )
    assert isinstance(draft, PlanDraft)
    assert len(draft.actions) > 0
    first_action = draft.actions[0]
    assert first_action.dept in ["stormwater", "power_utility", "sewerage", "traffic_police"]
    assert "ev-rain-01" in first_action.evidence_ids


def test_llm_structured_framework_ticket_draft():
    draft = LLM.structured(
        TicketDraft,
        prompt="Sparks from electric pole and blackout reported in Bellandur",
    )
    assert isinstance(draft, TicketDraft)
    assert draft.category == "power"
    assert draft.severity >= 3


def test_llm_direct_mode_openai_call():
    with patch("app.config.settings.LLM_BACKEND", "direct"), \
         patch("app.config.settings.OPENAI_API_KEY", "sk-mock-key"), \
         patch("httpx.Client.post") as mock_post:
        
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": '{"category": "waterlogging", "severity": 4, "location_hint": "Ecospace", "text_en": "Flooded street"}'
                    }
                }
            ]
        }
        mock_post.return_value = mock_resp

        draft = LLM.structured(
            TicketDraft,
            prompt="Water on street",
        )
        assert draft.category == "waterlogging"
        assert draft.severity == 4


def test_universal_adapter_translation():
    from app.intake.extract import translate
    res = translate("ಇಲ್ಲಿ ಭಾರಿ ಮಳೆ ಮತ್ತು ನೀರು ನಿಂತಿದೆ", source_lang="kn")
    assert "water" in res.lower() or "flood" in res.lower()

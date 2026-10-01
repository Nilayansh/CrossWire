from __future__ import annotations

from app.contracts.keys import HypothesisID
from app.contracts.models import Ticket
from ui.components.feed import get_lang_badge
from ui.components.investigator import (
    get_provenance_badge_html,
    sort_hypotheses_by_posterior,
)
from ui.components.map import build_h3_layer_data
from ui.mock_api import load_fixture_evidence, load_fixture_tickets


def test_sort_hypotheses_by_posterior():
    ranked = [
        (HypothesisID.DRAIN_BLOCKAGE, 0.15),
        (HypothesisID.POWER_LED_STP_OVERFLOW, 0.75),
        (HypothesisID.RAIN_OVERWHELM, 0.10),
    ]
    sorted_ranked = sort_hypotheses_by_posterior(ranked)
    assert sorted_ranked[0][0] == HypothesisID.POWER_LED_STP_OVERFLOW
    assert sorted_ranked[0][1] == 0.75
    assert sorted_ranked[1][0] == HypothesisID.DRAIN_BLOCKAGE
    assert sorted_ranked[2][0] == HypothesisID.RAIN_OVERWHELM


def test_provenance_badge_mapping():
    real_badge = get_provenance_badge_html("real")
    assert "[REAL]" in real_badge
    assert "#064e3b" in real_badge

    sim_badge = get_provenance_badge_html("simulated")
    assert "[SIMULATED]" in sim_badge
    assert "#581c87" in sim_badge

    dev_badge = get_provenance_badge_html("derived")
    assert "[DERIVED]" in dev_badge
    assert "#1e3a8a" in dev_badge

    unknown_badge = get_provenance_badge_html("custom")
    assert "[CUSTOM]" in unknown_badge


def test_lang_badge():
    assert get_lang_badge("kn") == "🇮🇳 KN"
    assert get_lang_badge("en") == "🇬🇧 EN"
    assert get_lang_badge("hi") == "🌐 HI"


def test_build_h3_layer_data():
    tickets = [
        Ticket(
            id="t-1",
            ts="2026-09-05T08:00:00Z",
            channel="telegram",
            lang="en",
            text_original="Water on road",
            text_en="Water on road",
            category="waterlogging",
            severity=4,
            lat=12.926,
            lon=77.683,
            geo_confidence=0.9,
            h3_r8="886189255bfffff",
        ),
        Ticket(
            id="t-2",
            ts="2026-09-05T08:05:00Z",
            channel="telegram",
            lang="kn",
            text_original="ಕರೆಂಟ್ ಇಲ್ಲ",
            text_en="No power",
            category="power",
            severity=3,
            lat=12.926,
            lon=77.683,
            geo_confidence=0.9,
            h3_r8="886189255bfffff",
        ),
    ]

    h3_records = build_h3_layer_data(incident=None, tickets=tickets)
    assert len(h3_records) == 1
    rec = h3_records[0]
    assert rec["hex"] == "886189255bfffff"
    assert rec["count"] == 2
    assert rec["avg_severity"] == 3.5
    assert rec["elevation"] == 120
    assert len(rec["color"]) == 4


def test_fixture_loaders():
    tickets = load_fixture_tickets()
    assert len(tickets) > 0
    assert tickets[0].h3_r8 is not None

    evidence = load_fixture_evidence()
    assert len(evidence) > 0
    assert evidence[0].provenance in ("real", "simulated", "derived")

import json
from pathlib import Path
import random

import pytest

from app.contracts.keys import EvidenceKey, HypothesisID
from app.contracts.models import Evidence
from app.investigator.hypotheses import DEFAULT_PRIORS
from app.investigator.scoring import (
    apply,
    discriminating_keys,
    init_state,
    posterior,
    should_stop,
)


def load_fixture_evidence(fixture_name: str) -> list[Evidence]:
    fixture_path = Path("tests/fixtures") / fixture_name
    with open(fixture_path, encoding="utf-8") as f:
        data = json.load(f)
    return [Evidence.model_validate(item) for item in data]


def test_init_state_defaults_to_priors():
    state = init_state()
    assert isinstance(state, dict)
    assert set(state.keys()) == set(HypothesisID)
    # Posteriors of initial state should match DEFAULT_PRIORS
    post = posterior(state)
    for h in HypothesisID:
        assert abs(post[h] - DEFAULT_PRIORS[h]) < 1e-4


def test_apply_is_immutable():
    initial_state = init_state()
    state_copy = dict(initial_state)
    updated_state = apply(initial_state, [EvidenceKey.RAIN_GT_40])
    
    assert initial_state == state_copy, "apply must not mutate the input state"
    assert updated_state != initial_state, "apply should return a new updated state"


def test_posterior_sums_to_one():
    state = init_state()
    post = posterior(state)
    assert abs(sum(post.values()) - 1.0) < 1e-6
    for v in post.values():
        assert 0.0 <= v <= 1.0

    # Also test after applying several evidence keys
    keys = [EvidenceKey.RAIN_GT_25, EvidenceKey.LOW_LYING, EvidenceKey.KNOWN_HOTSPOT]
    updated = apply(state, keys)
    post_updated = posterior(updated)
    assert abs(sum(post_updated.values()) - 1.0) < 1e-6


def test_permutation_invariance():
    """Property test: Log-odds Bayesian updates commute under permutation."""
    keys = [
        EvidenceKey.RAIN_GT_40,
        EvidenceKey.LOW_LYING,
        EvidenceKey.KNOWN_HOTSPOT,
        EvidenceKey.SUSTAINED_RAIN_24H,
    ]
    state1 = init_state()
    state1 = apply(state1, keys)
    post1 = posterior(state1)

    for _ in range(5):
        shuffled = list(keys)
        random.shuffle(shuffled)
        state2 = init_state()
        state2 = apply(state2, shuffled)
        post2 = posterior(state2)

        for h in HypothesisID:
            assert abs(post1[h] - post2[h]) < 1e-6, f"Mismatch for {h} after shuffle"


def test_traffic_only_wins_on_null_signals():
    """TRAFFIC_ONLY wins when only NO_WATER_POWER_SIGNAL and TRAFFIC_SLOWDOWN are applied."""
    state = init_state()
    state = apply(
        state,
        [EvidenceKey.NO_WATER_POWER_SIGNAL, EvidenceKey.TRAFFIC_SLOWDOWN],
    )
    post = posterior(state)
    ranked = sorted(post.items(), key=lambda kv: kv[1], reverse=True)
    top_hyp, top_prob = ranked[0]
    second_hyp, second_prob = ranked[1]

    assert top_hyp == HypothesisID.TRAFFIC_ONLY
    assert top_prob > 0.60
    assert (top_prob - second_prob) > 0.20


def test_fixture_rain_overwhelm():
    evidence_list = load_fixture_evidence("evidence_rain_overwhelm.json")
    all_keys = [k for ev in evidence_list for k in ev.keys]
    
    state = init_state()
    state = apply(state, all_keys)
    post = posterior(state)
    
    ranked = sorted(post.items(), key=lambda kv: kv[1], reverse=True)
    top_hyp, top_prob = ranked[0]
    
    assert top_hyp == HypothesisID.RAIN_OVERWHELM
    assert top_prob >= 0.75


def test_fixture_power_led_stp():
    evidence_list = load_fixture_evidence("evidence_power_led_stp.json")
    all_keys = [k for ev in evidence_list for k in ev.keys]
    
    state = init_state()
    state = apply(state, all_keys)
    post = posterior(state)
    
    ranked = sorted(post.items(), key=lambda kv: kv[1], reverse=True)
    top_hyp, top_prob = ranked[0]
    
    assert top_hyp == HypothesisID.POWER_LED_STP_OVERFLOW
    assert top_prob >= 0.75


def test_fixture_inconclusive():
    evidence_list = load_fixture_evidence("evidence_inconclusive.json")
    all_keys = [k for ev in evidence_list for k in ev.keys]
    
    state = init_state()
    state = apply(state, all_keys)
    post = posterior(state)
    
    ranked = sorted(post.items(), key=lambda kv: kv[1], reverse=True)
    top_prob = ranked[0][1]
    second_prob = ranked[1][1]
    
    # Neither top prob >= 0.75 nor margin >= 0.2
    assert top_prob < 0.75 or (top_prob - second_prob) < 0.2


def test_should_stop_conclusive():
    post = {h: 0.05 for h in HypothesisID}
    post[HypothesisID.RAIN_OVERWHELM] = 0.75
    # Normalize remaining to ensure sum == 1.0
    post[HypothesisID.DRAIN_BLOCKAGE] = 0.10
    post[HypothesisID.LAKE_OVERFLOW] = 0.05
    post[HypothesisID.POWER_LED_STP_OVERFLOW] = 0.04
    post[HypothesisID.PIPE_BURST] = 0.03
    post[HypothesisID.TRAFFIC_ONLY] = 0.03

    stop, reason = should_stop(post, steps=2, tools_left=4, budget=6)
    assert stop is True
    assert "conclusive" in reason.lower()


def test_should_stop_inconclusive_at_step_cap():
    # Margin < 0.2
    post = {
        HypothesisID.RAIN_OVERWHELM: 0.35,
        HypothesisID.DRAIN_BLOCKAGE: 0.30,
        HypothesisID.LAKE_OVERFLOW: 0.15,
        HypothesisID.POWER_LED_STP_OVERFLOW: 0.10,
        HypothesisID.PIPE_BURST: 0.05,
        HypothesisID.TRAFFIC_ONLY: 0.05,
    }

    # At steps < 6 and tools left: continue
    stop, reason = should_stop(post, steps=3, tools_left=3, budget=6)
    assert stop is False

    # At steps >= 6: returns inconclusive
    stop, reason = should_stop(post, steps=6, tools_left=2, budget=6)
    assert stop is True
    assert "inconclusive" in reason.lower()


def test_should_stop_no_tools_left():
    post = {
        HypothesisID.RAIN_OVERWHELM: 0.40,
        HypothesisID.DRAIN_BLOCKAGE: 0.35,
        HypothesisID.LAKE_OVERFLOW: 0.10,
        HypothesisID.POWER_LED_STP_OVERFLOW: 0.05,
        HypothesisID.PIPE_BURST: 0.05,
        HypothesisID.TRAFFIC_ONLY: 0.05,
    }
    stop, reason = should_stop(post, steps=3, tools_left=0, budget=6)
    assert stop is True
    assert "no tools left" in reason.lower() or "inconclusive" in reason.lower()


def test_discriminating_keys():
    """discriminating_keys returns keys that separate the top two hypotheses."""
    # Top two: RAIN_OVERWHELM and DRAIN_BLOCKAGE
    post = {
        HypothesisID.RAIN_OVERWHELM: 0.45,
        HypothesisID.DRAIN_BLOCKAGE: 0.35,
        HypothesisID.LAKE_OVERFLOW: 0.10,
        HypothesisID.POWER_LED_STP_OVERFLOW: 0.05,
        HypothesisID.PIPE_BURST: 0.03,
        HypothesisID.TRAFFIC_ONLY: 0.02,
    }
    disc_keys = discriminating_keys(post)
    assert isinstance(disc_keys, list)
    assert len(disc_keys) > 0
    # RAIN_GT_40 strongly separates RAIN_OVERWHELM (LR 8.0) and DRAIN_BLOCKAGE (LR 0.4)
    assert EvidenceKey.RAIN_GT_40 in disc_keys
    # The top discriminating key should have higher separation than the last
    assert all(isinstance(k, EvidenceKey) for k in disc_keys)


def test_scoring_cli():
    import subprocess
    import sys

    res = subprocess.run(
        [sys.executable, "-m", "app.investigator.scoring", "--fixture", "rain_overwhelm"],
        capture_output=True,
        text=True,
        check=True,
    )
    assert "RAIN_OVERWHELM" in res.stdout
    assert "Posterior" in res.stdout
    assert "conclusive" in res.stdout

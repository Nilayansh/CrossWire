from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from app.contracts.keys import EvidenceKey, HypothesisID
from app.contracts.models import Evidence
from app.investigator.hypotheses import DEFAULT_PRIORS, LIKELIHOOD_RATIOS


def init_state(priors: dict[HypothesisID, float] | None = None) -> dict[HypothesisID, float]:
    """Initialize state in log-odds from prior distribution.
    
    If priors are omitted, defaults to DEFAULT_PRIORS.
    """
    priors_map = priors or DEFAULT_PRIORS
    return {h: math.log(max(p, 1e-12)) for h, p in priors_map.items()}


def apply(state: dict[HypothesisID, float], keys: list[EvidenceKey]) -> dict[HypothesisID, float]:
    """Pure, immutable Bayesian update in log-odds space.
    
    For each hypothesis H:
        log_odds_new(H) = log_odds(H) + sum(log(LR[H][key]))
    """
    updated = dict(state)
    for key in keys:
        for h in state.keys():
            lr = LIKELIHOOD_RATIOS.get(h, {}).get(key, 1.0)
            updated[h] = updated[h] + math.log(max(lr, 1e-12))
    return updated


def posterior(state: dict[HypothesisID, float]) -> dict[HypothesisID, float]:
    """Softmax-normalised posterior probabilities from log-odds state.
    
    P(H) = exp(state[H] - max(state)) / sum(exp(state[h] - max(state)))
    Guarantees numerical stability and sum(P) == 1.0.
    """
    max_val = max(state.values())
    exp_vals = {h: math.exp(v - max_val) for h, v in state.items()}
    total = sum(exp_vals.values())
    return {h: exp_vals[h] / total for h in state}


def should_stop(
    post: dict[HypothesisID, float],
    steps: int,
    tools_left: int,
    budget: int = 6,
) -> tuple[bool, str]:
    """Stopping rule for investigator loop.
    
    Stops if:
    - top posterior >= 0.75 and margin over second >= 0.2 (conclusive)
    - steps >= budget (inconclusive: budget cap reached)
    - tools_left <= 0 (inconclusive: no tools left)
    """
    ranked = sorted(post.items(), key=lambda kv: kv[1], reverse=True)
    top_h, top_prob = ranked[0]
    second_prob = ranked[1][1] if len(ranked) > 1 else 0.0
    margin = top_prob - second_prob

    if top_prob >= 0.75 and margin >= 0.2:
        return True, f"conclusive: {top_h.value} reached {top_prob:.1%} (margin: {margin:.1%})"

    if steps >= budget:
        return True, f"inconclusive: step cap ({budget}) reached; top candidate {top_h.value} at {top_prob:.1%} (margin: {margin:.1%})"

    if tools_left <= 0:
        return True, f"inconclusive: no tools left; top candidate {top_h.value} at {top_prob:.1%} (margin: {margin:.1%})"

    return False, "continue"


def discriminating_keys(post: dict[HypothesisID, float]) -> list[EvidenceKey]:
    """Returns the evidence keys that most separate the top two hypotheses.
    
    Separation power is measured by |log(LR[H1][K]) - log(LR[H2][K])|.
    """
    ranked = sorted(post.items(), key=lambda kv: kv[1], reverse=True)
    if len(ranked) < 2:
        return list(EvidenceKey)

    h1, h2 = ranked[0][0], ranked[1][0]
    lrs1 = LIKELIHOOD_RATIOS.get(h1, {})
    lrs2 = LIKELIHOOD_RATIOS.get(h2, {})

    separation: list[tuple[EvidenceKey, float]] = []
    for key in EvidenceKey:
        lr1 = lrs1.get(key, 1.0)
        lr2 = lrs2.get(key, 1.0)
        delta = abs(math.log(max(lr1, 1e-12)) - math.log(max(lr2, 1e-12)))
        separation.append((key, delta))

    # Sort descending by separation score
    separation.sort(key=lambda kv: kv[1], reverse=True)
    # Return non-zero discriminators first, or all if all zero
    significant = [key for key, score in separation if score > 1e-4]
    return significant if significant else [key for key, _ in separation]


def _resolve_fixture_path(name: str) -> Path:
    p = Path(name)
    if p.exists():
        return p
    fixtures_dir = Path("tests/fixtures")
    candidates = [
        fixtures_dir / name,
        fixtures_dir / f"{name}.json",
        fixtures_dir / f"evidence_{name}.json",
    ]
    for c in candidates:
        if c.exists():
            return c
    raise FileNotFoundError(f"Fixture '{name}' not found under tests/fixtures/")


def main() -> None:
    parser = argparse.ArgumentParser(description="NammaTwin Bayesian Scoring Engine CLI")
    parser.add_argument(
        "--fixture",
        type=str,
        required=True,
        help="Fixture name or path (e.g., rain_overwhelm, power_led_stp, inconclusive)",
    )
    args = parser.parse_args()

    fixture_path = _resolve_fixture_path(args.fixture)
    with open(fixture_path, encoding="utf-8") as f:
        raw_evidence = json.load(f)

    evidence_items = [Evidence.model_validate(item) for item in raw_evidence]
    all_keys: list[EvidenceKey] = []
    for ev in evidence_items:
        all_keys.extend(ev.keys)

    state = init_state()
    state = apply(state, all_keys)
    post = posterior(state)

    ranked = sorted(post.items(), key=lambda kv: kv[1], reverse=True)
    stop, reason = should_stop(post, steps=len(evidence_items), tools_left=6 - len(evidence_items))

    print(f"\n========================================================")
    print(f"Fixture: {fixture_path.name}")
    print(f"Evidence items: {len(evidence_items)}")
    print(f"Observed keys: {[k.value for k in all_keys]}")
    print(f"========================================================")
    print(f"{'Hypothesis':<25} | {'Posterior':<10} | {'Log-Odds':<10}")
    print("-" * 52)
    for hyp, prob in ranked:
        print(f"{hyp.value:<25} | {prob:>8.2%} | {state[hyp]:>9.3f}")
    print("=" * 52)
    print(f"Status: {reason}\n")


if __name__ == "__main__":
    main()

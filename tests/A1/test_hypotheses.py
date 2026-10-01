from app.contracts.keys import EvidenceKey, HypothesisID
from app.investigator.hypotheses import (
    DEFAULT_PRIORS,
    HYPOTHESIS_DEPARTMENTS,
    LIKELIHOOD_RATIOS,
)


def test_hypotheses_catalog_coverage():
    """Verify all HypothesisIDs are covered in priors, LR, and department mappings."""
    for hyp in HypothesisID:
        assert hyp in DEFAULT_PRIORS, f"Missing prior for {hyp}"
        assert hyp in LIKELIHOOD_RATIOS, f"Missing LR table for {hyp}"
        assert hyp in HYPOTHESIS_DEPARTMENTS, f"Missing departments for {hyp}"
        assert len(HYPOTHESIS_DEPARTMENTS[hyp]) > 0, f"No departments assigned to {hyp}"


def test_priors_are_valid_probabilities():
    """Priors should be positive numbers summing to 1.0 (or valid non-zero prior distribution)."""
    assert len(DEFAULT_PRIORS) == len(HypothesisID)
    total = sum(DEFAULT_PRIORS.values())
    assert abs(total - 1.0) < 1e-6, f"Priors should sum to 1.0, got {total}"
    for hyp, p in DEFAULT_PRIORS.items():
        assert 0.0 < p < 1.0, f"Prior for {hyp} must be in (0, 1)"


def test_likelihood_ratios_are_positive():
    """Likelihood ratios P(E|H)/P(E|~H) must be strictly positive floats."""
    for hyp, lrs in LIKELIHOOD_RATIOS.items():
        assert isinstance(lrs, dict)
        for ev_key, lr in lrs.items():
            assert isinstance(ev_key, EvidenceKey)
            assert lr > 0.0, f"LR for ({hyp}, {ev_key}) must be positive, got {lr}"

from __future__ import annotations

from app.contracts.keys import EvidenceKey, HypothesisID

# Default uniform priors summing to 1.0
DEFAULT_PRIORS: dict[HypothesisID, float] = {
    HypothesisID.RAIN_OVERWHELM: 1.0 / 6.0,
    HypothesisID.DRAIN_BLOCKAGE: 1.0 / 6.0,
    HypothesisID.POWER_LED_STP_OVERFLOW: 1.0 / 6.0,
    HypothesisID.PIPE_BURST: 1.0 / 6.0,
    HypothesisID.LAKE_OVERFLOW: 1.0 / 6.0,
    HypothesisID.TRAFFIC_ONLY: 1.0 / 6.0,
}

# Mapping of hypothesis to responsible departments
HYPOTHESIS_DEPARTMENTS: dict[HypothesisID, list[str]] = {
    HypothesisID.RAIN_OVERWHELM: ["Stormwater", "Traffic"],
    HypothesisID.DRAIN_BLOCKAGE: ["Stormwater/SWD", "Solid Waste"],
    HypothesisID.POWER_LED_STP_OVERFLOW: ["Power utility", "Sewerage board"],
    HypothesisID.PIPE_BURST: ["Water board"],
    HypothesisID.LAKE_OVERFLOW: ["Lake authority", "Stormwater"],
    HypothesisID.TRAFFIC_ONLY: ["Traffic police"],
}

# Likelihood ratios: P(evidence | H) / P(evidence | ~H)
# LR > 1.0 supports H; LR < 1.0 refutes H; neutral is 1.0.
LIKELIHOOD_RATIOS: dict[HypothesisID, dict[EvidenceKey, float]] = {
    HypothesisID.RAIN_OVERWHELM: {
        EvidenceKey.RAIN_GT_40: 8.0,
        EvidenceKey.RAIN_GT_25: 6.0,
        EvidenceKey.SUSTAINED_RAIN_24H: 2.5,
        EvidenceKey.LOW_LYING: 2.5,
        EvidenceKey.KNOWN_HOTSPOT: 3.0,
        EvidenceKey.RAIN_LT_15: 0.2,
        EvidenceKey.RAIN_LT_5: 0.1,
        EvidenceKey.DRY_WEATHER: 0.05,
        EvidenceKey.NO_WATER_POWER_SIGNAL: 0.2,
    },
    HypothesisID.DRAIN_BLOCKAGE: {
        EvidenceKey.DEBRIS_TICKETS_NEARBY: 5.0,
        EvidenceKey.LOCALIZED_SPREAD: 2.5,
        EvidenceKey.KNOWN_HOTSPOT: 1.8,
        EvidenceKey.RAIN_LT_15: 2.5,
        EvidenceKey.RAIN_LT_5: 2.0,
        EvidenceKey.DRY_WEATHER: 1.5,
        EvidenceKey.RAIN_GT_40: 0.4,
        EvidenceKey.NO_WATER_POWER_SIGNAL: 0.3,
    },
    HypothesisID.POWER_LED_STP_OVERFLOW: {
        EvidenceKey.POWER_TICKETS_PRECEDE_SEWAGE: 7.0,
        EvidenceKey.OUTAGE_REPORTED: 5.0,
        EvidenceKey.LARGE_STP_SITE_NEARBY: 3.5,
        EvidenceKey.LOCALIZED_SPREAD: 1.5,
        EvidenceKey.DRY_WEATHER: 1.5,
        EvidenceKey.RAIN_GT_40: 0.5,
        EvidenceKey.NO_WATER_POWER_SIGNAL: 0.1,
    },
    HypothesisID.PIPE_BURST: {
        EvidenceKey.LINEAR_SPREAD: 5.0,
        EvidenceKey.LOCALIZED_SPREAD: 2.0,
        EvidenceKey.DRY_WEATHER: 3.5,
        EvidenceKey.RAIN_LT_5: 2.5,
        EvidenceKey.RAIN_GT_25: 0.3,
        EvidenceKey.RAIN_GT_40: 0.1,
        EvidenceKey.NO_WATER_POWER_SIGNAL: 0.2,
    },
    HypothesisID.LAKE_OVERFLOW: {
        EvidenceKey.NEAR_LAKE: 6.0,
        EvidenceKey.SUSTAINED_RAIN_24H: 4.5,
        EvidenceKey.RAIN_GT_25: 3.0,
        EvidenceKey.LOW_LYING: 2.5,
        EvidenceKey.DRY_WEATHER: 0.1,
        EvidenceKey.RAIN_LT_5: 0.2,
        EvidenceKey.NO_WATER_POWER_SIGNAL: 0.2,
    },
    HypothesisID.TRAFFIC_ONLY: {
        EvidenceKey.TRAFFIC_SLOWDOWN: 4.0,
        EvidenceKey.NO_WATER_POWER_SIGNAL: 6.0,
        EvidenceKey.DRY_WEATHER: 2.5,
        EvidenceKey.RAIN_GT_25: 0.2,
        EvidenceKey.RAIN_GT_40: 0.05,
        EvidenceKey.LOW_LYING: 0.5,
        EvidenceKey.POWER_TICKETS_PRECEDE_SEWAGE: 0.05,
        EvidenceKey.OUTAGE_REPORTED: 0.1,
        EvidenceKey.DEBRIS_TICKETS_NEARBY: 0.2,
    },
}

# Alias for spec compliance
LR = LIKELIHOOD_RATIOS

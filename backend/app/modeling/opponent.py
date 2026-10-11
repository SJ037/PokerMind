from __future__ import annotations

from dataclasses import dataclass, field
from math import tanh

from backend.app.modeling.bayesian import BetaEstimator


PROFILE_BASELINES: dict[str, dict[str, float]] = {
    "unknown": {"fold_vs_raise": 0.5, "raise_freq": 0.2, "cbet_freq": 0.5},
    "tight_passive": {"fold_vs_raise": 0.62, "raise_freq": 0.12, "cbet_freq": 0.45},
    "loose_passive": {"fold_vs_raise": 0.45, "raise_freq": 0.1, "cbet_freq": 0.4},
    "tight_aggressive": {"fold_vs_raise": 0.5, "raise_freq": 0.3, "cbet_freq": 0.62},
    "loose_aggressive": {"fold_vs_raise": 0.38, "raise_freq": 0.42, "cbet_freq": 0.68},
}


@dataclass(slots=True)
class OpponentProfile:
    opponent_id: str
    archetype: str = "unknown"
    fold_vs_raise: BetaEstimator = field(default_factory=BetaEstimator)
    raise_frequency: BetaEstimator = field(default_factory=BetaEstimator)
    cbet_frequency: BetaEstimator = field(default_factory=BetaEstimator)

    @classmethod
    def with_archetype(cls, opponent_id: str, archetype: str) -> "OpponentProfile":
        baseline = PROFILE_BASELINES.get(archetype, PROFILE_BASELINES["unknown"])

        def make_estimator(mean: float, prior_strength: float = 10.0) -> BetaEstimator:
            alpha = max(1.0, mean * prior_strength)
            beta = max(1.0, (1 - mean) * prior_strength)
            return BetaEstimator(alpha=alpha, beta=beta)

        return cls(
            opponent_id=opponent_id,
            archetype=archetype,
            fold_vs_raise=make_estimator(baseline["fold_vs_raise"]),
            raise_frequency=make_estimator(baseline["raise_freq"]),
            cbet_frequency=make_estimator(baseline["cbet_freq"]),
        )

    def observe(self, event: str, success: bool) -> None:
        if event == "fold_vs_raise":
            self.fold_vs_raise.observe(success)
        elif event == "raise":
            self.raise_frequency.observe(success)
        elif event == "cbet":
            self.cbet_frequency.observe(success)
        else:
            raise ValueError(f"Unknown event type: {event}")

    def response_probs(self, raise_size_to_pot: float) -> dict[str, float]:
        fold_base = self.fold_vs_raise.mean
        bet_pressure = tanh((raise_size_to_pot - 0.65) / 1.8)
        size_adjustment = 0.12 * bet_pressure
        fold_cap = 0.74 if raise_size_to_pot <= 1.5 else 0.68
        fold_floor = 0.08
        fold_p = min(fold_cap, max(fold_floor, fold_base + size_adjustment))

        aggression = self.raise_frequency.mean
        reraise_p = min(0.32, max(0.04, aggression * 0.65 * (1.0 - fold_p)))
        call_p = max(0.0, 1.0 - fold_p - reraise_p)

        total = fold_p + call_p + reraise_p
        return {
            "fold": fold_p / total,
            "call": call_p / total,
            "raise": reraise_p / total,
        }

    def to_dict(self) -> dict[str, object]:
        return {
            "opponent_id": self.opponent_id,
            "archetype": self.archetype,
            "fold_vs_raise": self.fold_vs_raise.as_dict(),
            "raise_frequency": self.raise_frequency.as_dict(),
            "cbet_frequency": self.cbet_frequency.as_dict(),
        }

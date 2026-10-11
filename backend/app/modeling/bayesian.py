from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class BetaEstimator:
    alpha: float = 2.0
    beta: float = 2.0

    def observe(self, success: bool) -> None:
        if success:
            self.alpha += 1.0
        else:
            self.beta += 1.0

    @property
    def mean(self) -> float:
        return self.alpha / (self.alpha + self.beta)

    @property
    def sample_size(self) -> float:
        return self.alpha + self.beta

    def as_dict(self) -> dict[str, float]:
        return {
            "alpha": self.alpha,
            "beta": self.beta,
            "mean": self.mean,
            "effective_n": self.sample_size,
        }

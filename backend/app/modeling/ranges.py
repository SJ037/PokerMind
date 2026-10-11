from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from backend.app.poker.cards import (
    all_two_card_combos,
    card_to_str,
    combo_to_key,
    key_to_combo,
)


@dataclass(slots=True)
class HandRange:
    weights: dict[tuple[int, int], float]

    def normalized(self) -> "HandRange":
        total = sum(max(weight, 0.0) for weight in self.weights.values())
        if total <= 0:
            raise ValueError("Range has no positive weights")
        return HandRange(
            {combo: max(weight, 0.0) / total for combo, weight in self.weights.items() if weight > 0}
        )

    def to_serializable(self, limit: int = 80) -> list[dict[str, float | str]]:
        sorted_items = sorted(self.weights.items(), key=lambda item: item[1], reverse=True)
        return [
            {"combo": combo_to_key(combo), "weight": round(weight, 6)}
            for combo, weight in sorted_items[:limit]
        ]


def create_uniform_range(excluded_cards: list[str]) -> HandRange:
    combos = all_two_card_combos(excluded_cards)
    uniform = {combo: 1.0 for combo in combos}
    return HandRange(uniform).normalized()


def hand_range_from_dict(weight_map: dict[str, float], excluded_cards: list[str]) -> HandRange:
    excluded = set(excluded_cards)
    parsed: dict[tuple[int, int], float] = {}
    for combo_key, weight in weight_map.items():
        combo = key_to_combo(combo_key)
        combo_cards = {card_to_str(combo[0]), card_to_str(combo[1])}
        if combo_cards & excluded:
            continue
        parsed[combo] = float(weight)
    if not parsed:
        return create_uniform_range(excluded_cards)
    return HandRange(parsed).normalized()


def update_range_bayes(
    prior: HandRange,
    action_likelihoods: dict[tuple[int, int], float],
) -> HandRange:
    posterior: dict[tuple[int, int], float] = {}
    for combo, prior_weight in prior.weights.items():
        likelihood = action_likelihoods.get(combo, 1e-6)
        posterior[combo] = max(prior_weight, 0.0) * max(likelihood, 0.0)
    return HandRange(posterior).normalized()


def sample_weighted_combo(hand_range: HandRange, rng: np.random.Generator) -> tuple[int, int]:
    normalized = hand_range.normalized()
    combos = list(normalized.weights.keys())
    probs = np.array([normalized.weights[combo] for combo in combos], dtype=np.float64)
    idx = int(rng.choice(len(combos), p=probs))
    return combos[idx]

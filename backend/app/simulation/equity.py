from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from backend.app.modeling.ranges import HandRange, sample_weighted_combo
from backend.app.poker.cards import create_deck, parse_card
from backend.app.poker.evaluator import compare_hands


@dataclass(slots=True)
class EquityResult:
    equity: float
    win_rate: float
    tie_rate: float
    loss_rate: float
    trials: int
    std_error: float


def estimate_equity(
    hero_cards: list[str],
    board_cards: list[str],
    hand_range: HandRange,
    trials: int = 15000,
    seed: int | None = None,
) -> EquityResult:
    rng = np.random.default_rng(seed)

    hero_ints = [parse_card(card) for card in hero_cards]
    board_ints = [parse_card(card) for card in board_cards]
    known = set(hero_ints + board_ints)

    wins = 0
    ties = 0
    losses = 0
    payoffs: list[float] = []

    total_board_cards = 5
    missing_board = total_board_cards - len(board_ints)

    for _ in range(trials):
        opp_combo = sample_weighted_combo(hand_range, rng)
        if opp_combo[0] in known or opp_combo[1] in known:
            continue

        dead = known | {opp_combo[0], opp_combo[1]}
        deck = [card for card in create_deck() if card not in dead]
        if missing_board > 0:
            runout = rng.choice(deck, size=missing_board, replace=False).tolist()
        else:
            runout = []
        final_board = board_ints + runout

        result = compare_hands(hero_ints, list(opp_combo), final_board)
        if result > 0:
            wins += 1
            payoffs.append(1.0)
        elif result < 0:
            losses += 1
            payoffs.append(0.0)
        else:
            ties += 1
            payoffs.append(0.5)

    completed = len(payoffs)
    if completed == 0:
        raise ValueError("No valid simulation trials completed")

    payoff_arr = np.array(payoffs)
    equity = float(np.mean(payoff_arr))
    std_error = float(np.std(payoff_arr, ddof=1) / np.sqrt(completed)) if completed > 1 else 0.0

    return EquityResult(
        equity=equity,
        win_rate=wins / completed,
        tie_rate=ties / completed,
        loss_rate=losses / completed,
        trials=completed,
        std_error=std_error,
    )

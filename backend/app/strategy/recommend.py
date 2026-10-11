from __future__ import annotations

from backend.app.modeling.opponent import OpponentProfile
from backend.app.poker.cards import parse_card
from backend.app.poker.evaluator import evaluate_seven_cards
from backend.app.poker.pots import PotState, legal_actions
from backend.app.simulation.equity import EquityResult
from backend.app.strategy.ev import ev_call, ev_fold, ev_raise


def _board_straight_threat(board_cards: list[str]) -> float:
    if len(board_cards) < 3:
        return 0.0
    ranks = sorted({card[0].upper() for card in board_cards})
    rank_value = {"2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7, "8": 8, "9": 9, "T": 10, "J": 11, "Q": 12, "K": 13, "A": 14}
    values = sorted({rank_value[rank] for rank in ranks})
    if 14 in values:
        values = [1] + values

    longest = 1
    current = 1
    for idx in range(1, len(values)):
        if values[idx] - values[idx - 1] <= 1:
            current += 1
        else:
            current = 1
        longest = max(longest, current)

    if len(board_cards) >= 5 and longest >= 5:
        return 1.0
    if longest >= 4:
        return 0.75
    if longest >= 3:
        return 0.45
    return 0.15


def _hero_made_rank(hero_cards: list[str], board_cards: list[str]) -> int:
    if len(hero_cards) != 2 or len(board_cards) < 3:
        return 0
    try:
        hero_ints = [parse_card(card) for card in hero_cards]
        board_ints = [parse_card(card) for card in board_cards]
    except ValueError:
        return 0
    rank_category, _ = evaluate_seven_cards(hero_ints + board_ints)
    return rank_category


def _street_from_board(board_cards: list[str]) -> str:
    count = len(board_cards)
    if count <= 3:
        return "flop"
    if count == 4:
        return "turn"
    return "river"


def _future_tree_terms(
    street: str,
    pot_after_action: float,
    opponent_profile: OpponentProfile,
    straight_threat: float,
    hero_rank_category: int,
) -> dict[str, float]:
    streets_left = 2 if street == "flop" else 1 if street == "turn" else 0
    if streets_left == 0:
        return {
            "streets_left": 0.0,
            "realization_factor": 1.0,
            "expected_future_cost": 0.0,
            "barrel_probability": 0.0,
            "bet_fraction": 0.0,
        }

    barrel_probability = min(
        0.88,
        max(
            0.20,
            0.35
            + 0.35 * opponent_profile.cbet_frequency.mean
            + 0.15 * opponent_profile.raise_frequency.mean
            + 0.10 * straight_threat,
        ),
    )

    if hero_rank_category <= 0:
        continue_rate = 0.35
    elif hero_rank_category == 1:
        continue_rate = 0.55
    else:
        continue_rate = 0.75

    bet_fraction = min(0.90, max(0.45, 0.60 + 0.15 * straight_threat))

    running_pot = max(1.0, float(pot_after_action))
    expected_future_cost = 0.0
    for idx in range(streets_left):
        step_prob = barrel_probability * (0.85**idx)
        step_cost = step_prob * bet_fraction * running_pot * continue_rate
        expected_future_cost += step_cost
        running_pot += step_prob * 2.0 * bet_fraction * running_pot * continue_rate

    realization_factor = 1.0
    realization_factor -= 0.08 * streets_left
    realization_factor -= 0.10 * straight_threat
    if hero_rank_category <= 0:
        realization_factor -= 0.06
    elif hero_rank_category == 1:
        realization_factor -= 0.02
    realization_factor = min(1.0, max(0.60, realization_factor))

    return {
        "streets_left": float(streets_left),
        "realization_factor": float(realization_factor),
        "expected_future_cost": float(expected_future_cost),
        "barrel_probability": float(barrel_probability),
        "bet_fraction": float(bet_fraction),
    }


def _normalize_response_probs(fold: float, call: float, raise_prob: float) -> dict[str, float]:
    fold = max(0.0, fold)
    call = max(0.0, call)
    raise_prob = max(0.0, raise_prob)
    total = max(1e-9, fold + call + raise_prob)
    return {
        "fold": fold / total,
        "call": call / total,
        "raise": raise_prob / total,
    }


def _branch_values(pot_at_decision: int, raise_amount: int, amount_to_call: int, equity_when_called: float) -> dict[str, float]:
    called_pot = pot_at_decision + (2 * raise_amount) - amount_to_call
    return {
        "fold": float(pot_at_decision),
        "call": float(equity_when_called * called_pot - raise_amount),
        "raise": float(-raise_amount),
    }


def _ev_from_branches(response_probs: dict[str, float], branch_values: dict[str, float]) -> float:
    return (
        response_probs["fold"] * branch_values["fold"]
        + response_probs["call"] * branch_values["call"]
        + response_probs["raise"] * branch_values["raise"]
    )


def _fold_sensitivity(
    base_probs: dict[str, float],
    branch_values: dict[str, float],
    delta: float = 0.10,
) -> dict[str, float]:
    base_fold = base_probs["fold"]
    remaining = max(1e-9, 1.0 - base_fold)
    call_share = base_probs["call"] / remaining
    raise_share = base_probs["raise"] / remaining

    low_fold = max(0.0, base_fold - delta)
    high_fold = min(0.95, base_fold + delta)

    low_remaining = 1.0 - low_fold
    high_remaining = 1.0 - high_fold

    low_probs = _normalize_response_probs(low_fold, low_remaining * call_share, low_remaining * raise_share)
    high_probs = _normalize_response_probs(high_fold, high_remaining * call_share, high_remaining * raise_share)

    low_ev = _ev_from_branches(low_probs, branch_values)
    high_ev = _ev_from_branches(high_probs, branch_values)
    return {
        "fold_prob_minus_10pp_ev": round(low_ev, 4),
        "fold_prob_plus_10pp_ev": round(high_ev, 4),
    }


def recommend_action(
    state: PotState,
    equity: EquityResult,
    opponent_profile: OpponentProfile,
    hero_cards: list[str] | None = None,
    board_cards: list[str] | None = None,
) -> dict[str, object]:
    actions = legal_actions(state)
    evaluations: list[dict[str, object]] = []
    board_cards = board_cards or []
    hero_cards = hero_cards or []
    straight_threat = _board_straight_threat(board_cards)
    hero_rank_category = _hero_made_rank(hero_cards, board_cards)
    street = _street_from_board(board_cards)

    for action in actions:
        name = str(action["action"])
        amount = int(action["amount"])
        risk_penalty = 0.0
        confidence_penalty = 0.0
        weak_hand_penalty = 0.0
        made_hand_penalty = 0.0
        raw_ev = 0.0
        adjusted_ev = 0.0
        branch_details: dict[str, object] = {}
        sensitivity: dict[str, float] | None = None
        if name == "fold":
            raw_ev = ev_fold()
            adjusted_ev = raw_ev
            assumptions = ["No additional chips invested"]
        elif name in {"call", "check"}:
            base_call_ev = ev_call(equity.equity, state.pot, state.amount_to_call)
            future_terms = _future_tree_terms(
                street=street,
                pot_after_action=state.pot + state.amount_to_call,
                opponent_profile=opponent_profile,
                straight_threat=straight_threat,
                hero_rank_category=hero_rank_category,
            )
            raw_ev = (
                ev_call(
                    equity.equity * future_terms["realization_factor"],
                    state.pot,
                    state.amount_to_call,
                )
                - future_terms["expected_future_cost"]
            )
            adjusted_ev = raw_ev
            branch_details = {
                "base_call_ev": round(base_call_ev, 4),
                "future_terms": {
                    "streets_left": future_terms["streets_left"],
                    "realization_factor": round(future_terms["realization_factor"], 4),
                    "expected_future_cost": round(future_terms["expected_future_cost"], 4),
                    "barrel_probability": round(future_terms["barrel_probability"], 4),
                    "bet_fraction": round(future_terms["bet_fraction"], 4),
                },
            }
            assumptions = ["Continuation-aware call EV approximation"]
        else:
            size_to_pot = amount / max(1, state.pot)
            base_response_probs = opponent_profile.response_probs(size_to_pot)
            invest_ratio = amount / max(1, state.hero_stack)

            raw_future_terms = _future_tree_terms(
                street=street,
                pot_after_action=state.pot + amount,
                opponent_profile=opponent_profile,
                straight_threat=straight_threat,
                hero_rank_category=hero_rank_category,
            )

            raw_branch_values = _branch_values(
                pot_at_decision=state.pot,
                raise_amount=amount,
                amount_to_call=state.amount_to_call,
                equity_when_called=equity.equity * raw_future_terms["realization_factor"],
            )
            raw_branch_values["call"] -= raw_future_terms["expected_future_cost"]

            if name == "all_in":
                base_response_probs = _normalize_response_probs(
                    base_response_probs["fold"],
                    base_response_probs["call"] + base_response_probs["raise"],
                    0.0,
                )

            raw_ev = _ev_from_branches(base_response_probs, raw_branch_values)

            adjusted_response_probs = dict(base_response_probs)
            if straight_threat >= 0.75:
                fold_reduction = min(0.25, 0.15 + 0.18 * straight_threat)
                adjusted_fold = max(0.05, adjusted_response_probs["fold"] - fold_reduction)
                redistributed = adjusted_response_probs["fold"] - adjusted_fold
                call_new = min(0.95, adjusted_response_probs["call"] + redistributed * 0.8)
                raise_new = max(0.0, 1.0 - adjusted_fold - call_new)
                adjusted_response_probs = _normalize_response_probs(adjusted_fold, call_new, raise_new)
            if name == "all_in":
                adjusted_response_probs = _normalize_response_probs(
                    adjusted_response_probs["fold"],
                    adjusted_response_probs["call"] + adjusted_response_probs["raise"],
                    0.0,
                )

            realization = max(0.72, 0.97 - 0.20 * invest_ratio)
            adjusted_future_terms = _future_tree_terms(
                street=street,
                pot_after_action=state.pot + amount,
                opponent_profile=opponent_profile,
                straight_threat=straight_threat,
                hero_rank_category=hero_rank_category,
            )
            adjusted_ev = ev_raise(
                equity_when_called=equity.equity * realization * adjusted_future_terms["realization_factor"],
                pot_at_decision=state.pot,
                raise_amount=amount,
                response_probs=adjusted_response_probs,
                amount_to_call=state.amount_to_call,
            )
            adjusted_ev -= adjusted_future_terms["expected_future_cost"] * adjusted_response_probs["call"]
            overbet_ratio = max(0.0, size_to_pot - 1.0)
            risk_penalty = (
                (0.02 + 0.07 * invest_ratio) * amount
                + (0.03 * overbet_ratio * state.pot)
            )
            if equity.equity < 0.30:
                weak_hand_penalty = (0.30 - equity.equity) * (amount + state.pot) * 1.1
            if hero_rank_category <= 0:
                made_hand_penalty += (0.22 + 0.40 * straight_threat) * amount * (0.6 + invest_ratio)
            elif hero_rank_category == 1 and straight_threat >= 0.75:
                made_hand_penalty += 0.10 * amount
            confidence_penalty = equity.std_error * (state.pot + amount) * (0.45 + 0.8 * invest_ratio)
            adjusted_ev = adjusted_ev - risk_penalty - confidence_penalty - weak_hand_penalty - made_hand_penalty

            branch_details = {
                "raw_response_probs": {
                    "fold": round(base_response_probs["fold"], 4),
                    "call": round(base_response_probs["call"], 4),
                    "raise": round(base_response_probs["raise"], 4),
                },
                "adjusted_response_probs": {
                    "fold": round(adjusted_response_probs["fold"], 4),
                    "call": round(adjusted_response_probs["call"], 4),
                    "raise": round(adjusted_response_probs["raise"], 4),
                },
                "branch_values": {
                    "fold": round(raw_branch_values["fold"], 4),
                    "call": round(raw_branch_values["call"], 4),
                    "raise": round(raw_branch_values["raise"], 4),
                },
                "future_terms": {
                    "streets_left": adjusted_future_terms["streets_left"],
                    "realization_factor": round(adjusted_future_terms["realization_factor"], 4),
                    "expected_future_cost": round(adjusted_future_terms["expected_future_cost"], 4),
                    "barrel_probability": round(adjusted_future_terms["barrel_probability"], 4),
                    "bet_fraction": round(adjusted_future_terms["bet_fraction"], 4),
                },
            }
            sensitivity = _fold_sensitivity(base_response_probs, raw_branch_values)

            assumptions = [
                "Continuation-aware branch model",
                "Opponent response from profile posterior",
                "Risk-adjusted for stack commitment and simulation uncertainty",
                "Board-texture and made-hand conservatism",
            ]

        total_penalty = risk_penalty + confidence_penalty + weak_hand_penalty + made_hand_penalty
        evaluations.append(
            {
                "action": name,
                "amount": amount,
                "raw_ev": round(raw_ev, 4),
                "adjusted_ev": round(adjusted_ev, 4),
                "ev": round(adjusted_ev, 4),
                "safeguard_penalty": round(total_penalty, 4),
                "safeguard_breakdown": {
                    "risk_penalty": round(risk_penalty, 4),
                    "confidence_penalty": round(confidence_penalty, 4),
                    "weak_hand_penalty": round(weak_hand_penalty, 4),
                    "board_texture_penalty": round(made_hand_penalty, 4),
                },
                "branch_details": branch_details,
                "sensitivity": sensitivity,
                "assumptions": assumptions,
            }
        )

    ordered = sorted(evaluations, key=lambda row: float(row["adjusted_ev"]), reverse=True)
    best = ordered[0]
    second_best = ordered[1] if len(ordered) > 1 else ordered[0]

    confidence_margin = max(
        2.0,
        1.5 * equity.std_error * max(1, state.pot + state.amount_to_call),
        0.02 * max(1, state.amount_to_call),
    )

    if str(best["action"]) in {"raise", "all_in"}:
        best_ev = float(best["adjusted_ev"])
        second_ev = float(second_best["adjusted_ev"])
        if best_ev <= second_ev + confidence_margin:
            best = second_best

    fold_row = next((row for row in ordered if str(row["action"]) == "fold"), None)
    if fold_row is not None and float(best["adjusted_ev"]) <= float(fold_row["adjusted_ev"]) + confidence_margin * 0.5:
        best = fold_row

    return {
        "recommended_action": best,
        "alternatives": ordered,
        "decision_layers": {
            "legality": "Legal actions generated from stack and minimum-raise constraints.",
            "raw_ev": "Raw EV uses pot-at-decision formulas and opponent response model without safeguards.",
            "safeguards": "Safeguard penalties are applied after raw EV and reported separately.",
        },
        "decision_controls": {
            "confidence_margin": round(confidence_margin, 4),
            "note": "Aggressive actions require clear EV separation after risk and uncertainty penalties.",
        },
        "equity": {
            "equity": equity.equity,
            "win_rate": equity.win_rate,
            "tie_rate": equity.tie_rate,
            "loss_rate": equity.loss_rate,
            "std_error": equity.std_error,
            "trials": equity.trials,
        },
    }

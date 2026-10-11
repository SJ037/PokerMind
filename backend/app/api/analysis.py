from __future__ import annotations

from fastapi import APIRouter, HTTPException

from backend.app.modeling.opponent import OpponentProfile
from backend.app.modeling.ranges import HandRange, create_uniform_range, hand_range_from_dict
from backend.app.poker.cards import combo_to_key, parse_card
from backend.app.poker.evaluator import evaluate_seven_cards
from backend.app.poker.pots import PotState
from backend.app.schemas.analysis import EquityRequest, HandState
from backend.app.simulation.equity import estimate_equity
from backend.app.storage.db import load_opponent
from backend.app.strategy.recommend import recommend_action

router = APIRouter()


HAND_CATEGORY_LABELS = {
    8: "Straight Flush",
    7: "Four of a Kind",
    6: "Full House",
    5: "Flush",
    4: "Straight",
    3: "Three of a Kind",
    2: "Two Pair",
    1: "One Pair",
    0: "High Card",
}


def _serialize_ranked_range_by_board(
    hand_range: HandRange,
    board_cards: list[str],
    limit: int = 80,
) -> tuple[list[dict[str, float | int | str]], dict[str, float | str] | None]:
    board_ints = [parse_card(card) for card in board_cards]
    scored: list[dict[str, object]] = []

    for combo, weight in hand_range.weights.items():
        strength_rank, tie_break = evaluate_seven_cards([combo[0], combo[1], *board_ints])
        scored.append(
            {
                "combo": combo_to_key(combo),
                "weight": float(weight),
                "strength_rank": strength_rank,
                "hand_category": HAND_CATEGORY_LABELS[strength_rank],
                "tie_break": tuple(tie_break),
            }
        )

    scored_sorted = sorted(
        scored,
        key=lambda item: (
            int(item["strength_rank"]),
            tuple(item["tie_break"]),
            float(item["weight"]),
        ),
        reverse=True,
    )

    serialized = [
        {
            "combo": str(item["combo"]),
            "weight": round(float(item["weight"]), 6),
            "strength_rank": int(item["strength_rank"]),
            "hand_category": str(item["hand_category"]),
        }
        for item in scored_sorted[:limit]
    ]

    if not scored_sorted:
        return serialized, None

    best_strength_rank = int(scored_sorted[0]["strength_rank"])
    best_category_prob = sum(
        float(item["weight"])
        for item in scored_sorted
        if int(item["strength_rank"]) == best_strength_rank
    )
    best_combo = scored_sorted[0]
    best_possible_hand = {
        "hand_category": HAND_CATEGORY_LABELS[best_strength_rank],
        "probability": round(best_category_prob, 6),
        "best_combo": str(best_combo["combo"]),
        "best_combo_probability": round(float(best_combo["weight"]), 6),
    }
    return serialized, best_possible_hand


@router.post("/equity")
def equity(req: EquityRequest) -> dict[str, float | int]:
    try:
        excluded = req.hero_cards + req.board_cards
        hand_range = (
            hand_range_from_dict(req.range_weights, excluded)
            if req.range_weights
            else create_uniform_range(excluded)
        )
        result = estimate_equity(
            hero_cards=req.hero_cards,
            board_cards=req.board_cards,
            hand_range=hand_range,
            trials=req.trials,
            seed=req.seed,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return {
        "equity": result.equity,
        "win_rate": result.win_rate,
        "tie_rate": result.tie_rate,
        "loss_rate": result.loss_rate,
        "trials": result.trials,
        "std_error": result.std_error,
    }


@router.post("/analyze")
def analyze(req: HandState) -> dict[str, object]:
    try:
        excluded = req.hero_cards + req.board_cards
        hand_range = (
            hand_range_from_dict(req.range_weights, excluded)
            if req.range_weights
            else create_uniform_range(excluded)
        )

        equity_result = estimate_equity(
            hero_cards=req.hero_cards,
            board_cards=req.board_cards,
            hand_range=hand_range,
            trials=req.simulation_trials,
            seed=req.seed,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    persisted = load_opponent(req.opponent_id)
    if persisted:
        profile = OpponentProfile.with_archetype(req.opponent_id, str(persisted.get("archetype", "unknown")))
        profile.fold_vs_raise.alpha = float(persisted["fold_vs_raise"]["alpha"])
        profile.fold_vs_raise.beta = float(persisted["fold_vs_raise"]["beta"])
        profile.raise_frequency.alpha = float(persisted["raise_frequency"]["alpha"])
        profile.raise_frequency.beta = float(persisted["raise_frequency"]["beta"])
        profile.cbet_frequency.alpha = float(persisted["cbet_frequency"]["alpha"])
        profile.cbet_frequency.beta = float(persisted["cbet_frequency"]["beta"])
    else:
        profile = OpponentProfile.with_archetype(req.opponent_id, "unknown")

    state = PotState(
        pot=req.pot,
        amount_to_call=req.amount_to_call,
        hero_stack=req.hero_stack,
        opponent_stack=req.opponent_stack,
        min_raise_to=req.min_raise_to if req.min_raise_to > 0 else max(req.amount_to_call * 2, 1),
    )

    report = recommend_action(
        state=state,
        equity=equity_result,
        opponent_profile=profile,
        hero_cards=req.hero_cards,
        board_cards=req.board_cards,
    )

    ranked_range, best_possible_hand = _serialize_ranked_range_by_board(
        hand_range,
        req.board_cards,
    )

    return {
        "decision_report": report,
        "opponent_profile": profile.to_dict(),
        "top_range_combos": ranked_range,
        "best_possible_hand": best_possible_hand,
        "assumptions": [
            "Heads-up postflop model",
            "Continuation-aware branch approximation for flop/turn future pressure",
            "Monte Carlo showdown equity approximation",
        ],
    }

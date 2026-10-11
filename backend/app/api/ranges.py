from __future__ import annotations

from fastapi import APIRouter, HTTPException

from backend.app.modeling.ranges import create_uniform_range, hand_range_from_dict, update_range_bayes
from backend.app.poker.cards import parse_card
from backend.app.poker.evaluator import evaluate_seven_cards
from backend.app.schemas.analysis import RangeUpdateRequest

router = APIRouter()


@router.post("/ranges/update")
def update_range(req: RangeUpdateRequest) -> dict[str, object]:
    try:
        excluded = req.hero_cards + req.board_cards
        prior = (
            hand_range_from_dict(req.range_weights, excluded)
            if req.range_weights
            else create_uniform_range(excluded)
        )

        board_ints = [parse_card(card) for card in req.board_cards]

        action_likelihoods: dict[tuple[int, int], float] = {}
        for combo, _ in prior.weights.items():
            if len(board_ints) >= 3:
                opp_cards = [combo[0], combo[1]]
                strength_rank, tie_break = evaluate_seven_cards(opp_cards + board_ints)
                strength = strength_rank + (sum(tie_break[:2]) / 30.0 if tie_break else 0.0)
            else:
                strength = 2.0

            if req.action in {"bet", "raise"}:
                likelihood = min(0.98, 0.15 + 0.08 * strength)
            elif req.action in {"call", "check"}:
                likelihood = min(0.95, 0.25 + 0.05 * strength)
            else:
                likelihood = max(0.02, 0.7 - 0.08 * strength)
            action_likelihoods[combo] = likelihood

        posterior = update_range_bayes(prior, action_likelihoods)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return {
        "updated_range": posterior.to_serializable(),
        "normalization_mass": round(sum(posterior.weights.values()), 6),
    }

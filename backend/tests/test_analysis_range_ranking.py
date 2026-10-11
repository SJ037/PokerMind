from __future__ import annotations

from backend.app.api.analysis import _serialize_ranked_range_by_board
from backend.app.modeling.ranges import hand_range_from_dict


def test_top_range_combos_ranked_by_board_strength_not_only_weight() -> None:
    board_cards = ["Ah", "Kh", "Qh", "2c", "3d"]
    hand_range = hand_range_from_dict(
        {
            "JhTh": 0.02,
            "AdAc": 0.30,
            "7s7d": 0.68,
        },
        excluded_cards=board_cards,
    )

    ranked, best = _serialize_ranked_range_by_board(hand_range, board_cards, limit=3)

    assert len(ranked) == 3

    top = ranked[0]
    top_cards = {top["combo"][:2], top["combo"][2:]}
    assert top_cards == {"Jh", "Th"}
    assert top["hand_category"] == "Straight Flush"

    assert ranked[1]["hand_category"] == "Three of a Kind"
    assert ranked[2]["hand_category"] == "One Pair"

    assert best is not None
    assert best["hand_category"] == "Straight Flush"
    assert best["best_combo"] in {"ThJh", "JhTh"}
    assert abs(float(best["probability"]) - 0.02) < 1e-9
    assert abs(float(best["best_combo_probability"]) - 0.02) < 1e-9

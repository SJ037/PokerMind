from backend.app.poker.cards import parse_card
from backend.app.poker.evaluator import evaluate_five_cards


def test_straight_flush_beats_four_kind_category() -> None:
    straight_flush = [parse_card(c) for c in ["As", "Ks", "Qs", "Js", "Ts"]]
    four_kind = [parse_card(c) for c in ["Ah", "Ad", "Ac", "As", "2d"]]

    sf_rank = evaluate_five_cards(straight_flush)
    fk_rank = evaluate_five_cards(four_kind)

    assert sf_rank > fk_rank

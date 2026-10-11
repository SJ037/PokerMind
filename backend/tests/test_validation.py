import pytest
from pydantic import ValidationError

from backend.app.schemas.analysis import HandState


def test_handstate_rejects_duplicate_cards() -> None:
    with pytest.raises(ValidationError):
        HandState(
            hero_cards=["As", "Kh"],
            board_cards=["7s", "8s", "As"],
            pot=100,
            amount_to_call=20,
            hero_stack=500,
            opponent_stack=500,
            street="flop",
            position="ip",
            opponent_id="v1",
        )


def test_handstate_rejects_bad_card_string() -> None:
    with pytest.raises(ValidationError):
        HandState(
            hero_cards=["1x", "Kh"],
            board_cards=["7s", "8s", "2d"],
            pot=100,
            amount_to_call=20,
            hero_stack=500,
            opponent_stack=500,
            street="flop",
            position="ip",
            opponent_id="v1",
        )


def test_handstate_rejects_street_board_mismatch() -> None:
    with pytest.raises(ValidationError):
        HandState(
            hero_cards=["As", "Kh"],
            board_cards=["7s", "8s", "2d", "Qc"],
            pot=100,
            amount_to_call=20,
            hero_stack=500,
            opponent_stack=500,
            street="flop",
            position="ip",
            opponent_id="v1",
        )

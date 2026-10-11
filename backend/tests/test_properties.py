from hypothesis import given
from hypothesis import strategies as st

from backend.app.poker.cards import create_deck


@given(st.integers(min_value=0, max_value=100))
def test_deck_invariants(_: int) -> None:
    deck = create_deck()
    assert len(deck) == 52
    assert len(set(deck)) == 52

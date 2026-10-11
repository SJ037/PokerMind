from backend.app.poker.cards import card_to_str, create_deck, ensure_unique_cards, parse_card


def test_deck_has_52_unique_cards() -> None:
    deck = create_deck()
    assert len(deck) == 52
    assert len(set(deck)) == 52


def test_card_parse_roundtrip() -> None:
    card = "As"
    parsed = parse_card(card)
    assert card_to_str(parsed) == card


def test_duplicate_cards_rejected() -> None:
    try:
        ensure_unique_cards(["As", "As"])
    except ValueError:
        assert True
    else:
        assert False

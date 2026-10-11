from __future__ import annotations

from itertools import combinations

RANKS = "23456789TJQKA"
SUITS = "cdhs"
RANK_TO_VALUE = {rank: idx + 2 for idx, rank in enumerate(RANKS)}


def parse_card(card: str) -> int:
    if len(card) != 2:
        raise ValueError(f"Invalid card format: {card}")
    rank, suit = card[0].upper(), card[1].lower()
    if rank not in RANKS or suit not in SUITS:
        raise ValueError(f"Invalid card: {card}")
    rank_idx = RANKS.index(rank)
    suit_idx = SUITS.index(suit)
    return rank_idx * 4 + suit_idx


def card_to_str(card_int: int) -> str:
    if card_int < 0 or card_int > 51:
        raise ValueError(f"Card integer out of range: {card_int}")
    rank_idx, suit_idx = divmod(card_int, 4)
    return f"{RANKS[rank_idx]}{SUITS[suit_idx]}"


def create_deck() -> list[int]:
    return list(range(52))


def ensure_unique_cards(card_strs: list[str]) -> None:
    parsed = [parse_card(card) for card in card_strs]
    if len(parsed) != len(set(parsed)):
        raise ValueError("Duplicate card detected")


def remove_known_cards(deck: list[int], known_cards: list[str]) -> list[int]:
    known = {parse_card(card) for card in known_cards}
    return [card for card in deck if card not in known]


def canonical_combo(card_a: int, card_b: int) -> tuple[int, int]:
    return tuple(sorted((card_a, card_b)))


def combo_to_key(combo: tuple[int, int]) -> str:
    first, second = combo
    return f"{card_to_str(first)}{card_to_str(second)}"


def key_to_combo(combo_key: str) -> tuple[int, int]:
    if len(combo_key) != 4:
        raise ValueError(f"Invalid combo key: {combo_key}")
    first = parse_card(combo_key[:2])
    second = parse_card(combo_key[2:])
    if first == second:
        raise ValueError(f"Invalid combo key with duplicate cards: {combo_key}")
    return canonical_combo(first, second)


def all_two_card_combos(excluded_cards: list[str] | None = None) -> list[tuple[int, int]]:
    excluded = set(parse_card(card) for card in (excluded_cards or []))
    available = [card for card in create_deck() if card not in excluded]
    return [canonical_combo(a, b) for a, b in combinations(available, 2)]

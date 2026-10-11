from __future__ import annotations

from itertools import combinations

from backend.app.poker.cards import RANK_TO_VALUE, card_to_str


def _card_rank(card_int: int) -> int:
    return RANK_TO_VALUE[card_to_str(card_int)[0]]


def _card_suit(card_int: int) -> str:
    return card_to_str(card_int)[1]


def _is_straight(ranks: list[int]) -> tuple[bool, int]:
    unique = sorted(set(ranks), reverse=True)
    if len(unique) < 5:
        return False, 0
    if unique == [14, 5, 4, 3, 2]:
        return True, 5
    if unique[0] - unique[-1] == 4 and len(unique) == 5:
        return True, unique[0]
    return False, 0


def evaluate_five_cards(cards: list[int]) -> tuple[int, list[int]]:
    if len(cards) != 5:
        raise ValueError("Exactly 5 cards required")

    ranks = sorted((_card_rank(card) for card in cards), reverse=True)
    suits = [_card_suit(card) for card in cards]

    rank_counts: dict[int, int] = {}
    for rank in ranks:
        rank_counts[rank] = rank_counts.get(rank, 0) + 1

    is_flush = len(set(suits)) == 1
    straight, top_straight = _is_straight(ranks)

    count_rank_pairs = sorted(
        ((count, rank) for rank, count in rank_counts.items()), reverse=True
    )

    if straight and is_flush:
        return 8, [top_straight]

    if count_rank_pairs[0][0] == 4:
        four_rank = count_rank_pairs[0][1]
        kicker = [rank for rank in ranks if rank != four_rank][0]
        return 7, [four_rank, kicker]

    if count_rank_pairs[0][0] == 3 and count_rank_pairs[1][0] == 2:
        return 6, [count_rank_pairs[0][1], count_rank_pairs[1][1]]

    if is_flush:
        return 5, ranks

    if straight:
        return 4, [top_straight]

    if count_rank_pairs[0][0] == 3:
        trips = count_rank_pairs[0][1]
        kickers = sorted([rank for rank in ranks if rank != trips], reverse=True)
        return 3, [trips] + kickers

    if count_rank_pairs[0][0] == 2 and count_rank_pairs[1][0] == 2:
        pair_high = max(count_rank_pairs[0][1], count_rank_pairs[1][1])
        pair_low = min(count_rank_pairs[0][1], count_rank_pairs[1][1])
        kicker = [rank for rank in ranks if rank != pair_high and rank != pair_low][0]
        return 2, [pair_high, pair_low, kicker]

    if count_rank_pairs[0][0] == 2:
        pair_rank = count_rank_pairs[0][1]
        kickers = sorted([rank for rank in ranks if rank != pair_rank], reverse=True)
        return 1, [pair_rank] + kickers

    return 0, ranks


def evaluate_seven_cards(cards: list[int]) -> tuple[int, list[int]]:
    if len(cards) < 5 or len(cards) > 7:
        raise ValueError("5 to 7 cards required")
    best_rank: tuple[int, list[int]] | None = None
    for combo in combinations(cards, 5):
        rank = evaluate_five_cards(list(combo))
        if best_rank is None or rank > best_rank:
            best_rank = rank
    if best_rank is None:
        raise ValueError("Unable to evaluate cards")
    return best_rank


def compare_hands(hero_cards: list[int], villain_cards: list[int], board_cards: list[int]) -> int:
    hero_rank = evaluate_seven_cards(hero_cards + board_cards)
    villain_rank = evaluate_seven_cards(villain_cards + board_cards)
    if hero_rank > villain_rank:
        return 1
    if hero_rank < villain_rank:
        return -1
    return 0

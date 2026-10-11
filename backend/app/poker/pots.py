from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class PotState:
    pot: int
    amount_to_call: int
    hero_stack: int
    opponent_stack: int
    min_raise_to: int


def pot_odds(amount_to_call: int, current_pot: int) -> float:
    if amount_to_call <= 0:
        return 0.0
    return amount_to_call / (current_pot + amount_to_call)


def legal_actions(state: PotState) -> list[dict[str, int | str]]:
    actions: list[dict[str, int | str]] = [{"action": "fold", "amount": 0}]
    max_matchable_invest = min(state.hero_stack, state.amount_to_call + state.opponent_stack)

    if state.amount_to_call == 0:
        actions.append({"action": "check", "amount": 0})
    else:
        call_amount = min(state.amount_to_call, max_matchable_invest)
        actions.append({"action": "call", "amount": call_amount})

    if max_matchable_invest > state.amount_to_call:
        min_raise_to = max(state.min_raise_to, state.amount_to_call * 2)
        if min_raise_to <= max_matchable_invest:
            actions.append({"action": "raise", "amount": min_raise_to})
            medium = min(max_matchable_invest, max(min_raise_to, int(state.pot * 0.75)))
            large = min(max_matchable_invest, max(min_raise_to, int(state.pot * 1.5)))
            for candidate in (medium, large):
                if candidate > min_raise_to:
                    actions.append({"action": "raise", "amount": candidate})
        actions.append({"action": "all_in", "amount": max_matchable_invest})

    deduped: dict[tuple[str, int], dict[str, int | str]] = {}
    for action in actions:
        key = (str(action["action"]), int(action["amount"]))
        deduped[key] = action
    return list(deduped.values())

from __future__ import annotations


def ev_fold() -> float:
    return 0.0


def ev_call(equity: float, pot_at_decision: int, amount_to_call: int) -> float:
    final_pot = pot_at_decision + amount_to_call
    return equity * final_pot - amount_to_call


def ev_raise(
    equity_when_called: float,
    pot_at_decision: int,
    raise_amount: int,
    response_probs: dict[str, float],
    amount_to_call: int,
) -> float:
    fold_p = response_probs["fold"]
    call_p = response_probs["call"]
    reraise_p = response_probs["raise"]

    value_if_fold = pot_at_decision

    called_pot = pot_at_decision + (2 * raise_amount) - amount_to_call
    value_if_called = equity_when_called * called_pot - raise_amount

    value_if_reraised = -raise_amount

    return fold_p * value_if_fold + call_p * value_if_called + reraise_p * value_if_reraised

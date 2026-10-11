from backend.app.strategy.ev import ev_call, ev_raise


def test_ev_call_uses_pot_at_decision() -> None:
    ev = ev_call(equity=0.5, pot_at_decision=120, amount_to_call=40)
    assert ev == 40.0


def test_ev_raise_called_pot_math() -> None:
    ev = ev_raise(
        equity_when_called=0.5,
        pot_at_decision=120,
        raise_amount=100,
        response_probs={"fold": 0.0, "call": 1.0, "raise": 0.0},
        amount_to_call=40,
    )
    assert ev == 40.0

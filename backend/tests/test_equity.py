from backend.app.modeling.ranges import create_uniform_range
from backend.app.simulation.equity import estimate_equity


def test_equity_output_bounds() -> None:
    hero = ["As", "Ah"]
    board: list[str] = []
    hand_range = create_uniform_range(hero + board)

    result = estimate_equity(hero, board, hand_range, trials=1500, seed=7)

    assert 0.0 <= result.equity <= 1.0
    assert 0.0 <= result.win_rate <= 1.0
    assert 0.0 <= result.tie_rate <= 1.0
    assert 0.0 <= result.loss_rate <= 1.0
    assert result.trials > 0

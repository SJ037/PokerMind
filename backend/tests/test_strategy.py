from backend.app.modeling.opponent import OpponentProfile
from backend.app.poker.pots import PotState
from backend.app.simulation.equity import EquityResult
from backend.app.strategy.recommend import recommend_action


def test_recommendation_has_non_empty_actions() -> None:
    profile = OpponentProfile.with_archetype("v1", "unknown")
    state = PotState(pot=100, amount_to_call=25, hero_stack=500, opponent_stack=500, min_raise_to=50)
    equity = EquityResult(
        equity=0.55,
        win_rate=0.51,
        tie_rate=0.08,
        loss_rate=0.41,
        trials=5000,
        std_error=0.01,
    )
    report = recommend_action(state, equity, profile)
    assert "recommended_action" in report
    assert len(report["alternatives"]) > 0
    assert "decision_layers" in report
    assert "raw_ev" in report["alternatives"][0]
    assert "adjusted_ev" in report["alternatives"][0]


def test_recommends_fold_for_very_low_equity_spot() -> None:
    profile = OpponentProfile.with_archetype("v2", "unknown")
    state = PotState(pot=120, amount_to_call=50, hero_stack=600, opponent_stack=600, min_raise_to=100)
    equity = EquityResult(
        equity=0.12,
        win_rate=0.11,
        tie_rate=0.02,
        loss_rate=0.87,
        trials=6000,
        std_error=0.01,
    )
    report = recommend_action(state, equity, profile)
    assert report["recommended_action"]["action"] == "fold"


def test_does_not_default_to_all_in_when_uncertain() -> None:
    profile = OpponentProfile.with_archetype("v3", "unknown")
    state = PotState(pot=90, amount_to_call=20, hero_stack=1000, opponent_stack=1000, min_raise_to=40)
    equity = EquityResult(
        equity=0.46,
        win_rate=0.44,
        tie_rate=0.04,
        loss_rate=0.52,
        trials=2000,
        std_error=0.03,
    )
    report = recommend_action(state, equity, profile)
    assert report["recommended_action"]["action"] != "all_in"


def test_scary_connected_board_discourages_bluff_raise() -> None:
    profile = OpponentProfile.with_archetype("v4", "unknown")
    state = PotState(pot=140, amount_to_call=40, hero_stack=700, opponent_stack=700, min_raise_to=80)
    equity = EquityResult(
        equity=0.28,
        win_rate=0.24,
        tie_rate=0.08,
        loss_rate=0.68,
        trials=10000,
        std_error=0.012,
    )
    report = recommend_action(
        state,
        equity,
        profile,
        hero_cards=["As", "Kd"],
        board_cards=["9h", "Th", "Jc", "Qd", "2s"],
    )
    assert report["recommended_action"]["action"] in {"fold", "call"}


def test_aggressive_actions_include_branch_and_sensitivity_details() -> None:
    profile = OpponentProfile.with_archetype("v5", "unknown")
    state = PotState(pot=150, amount_to_call=30, hero_stack=600, opponent_stack=600, min_raise_to=60)
    equity = EquityResult(
        equity=0.51,
        win_rate=0.48,
        tie_rate=0.06,
        loss_rate=0.46,
        trials=9000,
        std_error=0.012,
    )
    report = recommend_action(
        state,
        equity,
        profile,
        hero_cards=["Ac", "Jd"],
        board_cards=["9h", "7c", "2d", "Qs"],
    )

    aggressive = [row for row in report["alternatives"] if row["action"] in {"raise", "all_in"}]
    assert aggressive
    first = aggressive[0]
    assert "branch_details" in first and first["branch_details"]
    assert "sensitivity" in first and first["sensitivity"]


def test_call_branch_includes_future_terms_on_flop() -> None:
    profile = OpponentProfile.with_archetype("v6", "unknown")
    state = PotState(pot=110, amount_to_call=30, hero_stack=500, opponent_stack=500, min_raise_to=60)
    equity = EquityResult(
        equity=0.5,
        win_rate=0.46,
        tie_rate=0.08,
        loss_rate=0.46,
        trials=8000,
        std_error=0.012,
    )
    report = recommend_action(
        state,
        equity,
        profile,
        hero_cards=["Ah", "7d"],
        board_cards=["9c", "Ts", "2h"],
    )
    call_rows = [row for row in report["alternatives"] if row["action"] == "call"]
    assert call_rows
    call_row = call_rows[0]
    assert "future_terms" in call_row["branch_details"]
    assert call_row["branch_details"]["future_terms"]["streets_left"] >= 1

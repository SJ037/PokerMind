from backend.app.poker.pots import PotState, legal_actions


def test_legal_actions_capped_by_effective_stack() -> None:
    state = PotState(pot=100, amount_to_call=40, hero_stack=900, opponent_stack=60, min_raise_to=80)
    actions = legal_actions(state)

    all_in = [action for action in actions if action["action"] == "all_in"]
    assert all_in
    assert all_in[0]["amount"] == 100

    raises = [int(action["amount"]) for action in actions if action["action"] == "raise"]
    assert all(amount <= 100 for amount in raises)


def test_no_raise_when_effective_stack_too_short() -> None:
    state = PotState(pot=90, amount_to_call=40, hero_stack=300, opponent_stack=20, min_raise_to=80)
    actions = legal_actions(state)
    assert not [action for action in actions if action["action"] == "raise"]

    all_in = [action for action in actions if action["action"] == "all_in"]
    assert all_in and int(all_in[0]["amount"]) == 60

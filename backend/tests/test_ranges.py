from backend.app.modeling.ranges import HandRange, update_range_bayes
from backend.app.poker.cards import all_two_card_combos


def test_range_update_normalizes() -> None:
    combos = all_two_card_combos(["As", "Kh"])
    base = {combo: 1.0 for combo in combos[:50]}
    prior = HandRange(base).normalized()

    likes = {combo: 0.8 if idx % 2 == 0 else 0.2 for idx, combo in enumerate(prior.weights.keys())}
    post = update_range_bayes(prior, likes)

    assert abs(sum(post.weights.values()) - 1.0) < 1e-8

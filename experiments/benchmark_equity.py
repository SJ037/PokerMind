from __future__ import annotations

import time

from backend.app.modeling.ranges import create_uniform_range
from backend.app.simulation.equity import estimate_equity


def main() -> None:
    hero = ["As", "Kh"]
    board = ["7s", "8s", "2d"]
    hand_range = create_uniform_range(hero + board)

    start = time.perf_counter()
    result = estimate_equity(hero, board, hand_range, trials=10000, seed=123)
    elapsed = time.perf_counter() - start

    print(
        {
            "equity": round(result.equity, 4),
            "std_error": round(result.std_error, 5),
            "trials": result.trials,
            "seconds": round(elapsed, 3),
        }
    )


if __name__ == "__main__":
    main()

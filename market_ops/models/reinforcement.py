from typing import Dict


def update_strategy(
    strategy: Dict[str, float], outcome: float, lr: float = 0.1
) -> Dict[str, float]:
    """Adjust a simple strategy dictionary based on an observed outcome.

    ``strategy`` maps symbols to their current score/weight; ``outcome`` is a
    numeric result (e.g. profit/loss) associated with the most recent action.
    The update rule uses a basic gradient step toward the observed value.
    """
    for sym, val in strategy.items():
        strategy[sym] = val + lr * (outcome - val)
    return strategy

from decimal import Decimal

from beancount.core.number import ZERO


def compute_returns(initial_value: Decimal, final_value: Decimal) -> float:
    if initial_value == ZERO:
        return 0.0
    return float((final_value - initial_value) / initial_value)


def annualize_returns(returns: float, years: float) -> float:
    if years == 0:
        return 0.0

    base = 1 + returns
    exp = 1 / years

    if base >= 0:
        return base**exp - 1
    else:
        # handle negative root
        return -((-base) ** exp - 1)

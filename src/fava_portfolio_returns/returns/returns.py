from decimal import Decimal

from beancount.core.number import ZERO


def compute_returns(initial_value: Decimal, final_value: Decimal):
    return (final_value - initial_value) / initial_value if initial_value != ZERO else ZERO


def compute_annualized_returns(returns: Decimal, years: Decimal):
    if years == 0:
        return 0

    base = 1 + returns
    exp = 1 / years

    if base >= 0:
        return base**exp - 1
    else:
        # handle negative root
        return -((-base) ** exp - 1)

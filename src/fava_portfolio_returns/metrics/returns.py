import datetime
import logging
from decimal import Decimal

from beancount.core.number import ZERO

from fava_portfolio_returns.api.portfolio import portfolio_values
from fava_portfolio_returns.core.portfolio import FilteredPortfolio
from fava_portfolio_returns.metrics.base import MetricBase
from fava_portfolio_returns.metrics.base import Series

logger = logging.getLogger(__name__)


class Returns(MetricBase):
    """
    Return compares the market value with the cost value

    single() is not implemented, because it doesn't make sense in some cases:
    * comparing market value with cash_in-cash_out: cash_in-cash_out can be negative at a specific date, but we still own stocks
    * comparing market value with cash_in: deposit X, withdraw Y, comparing X with market value Z doesn't make sense
    """

    def series(self, p: FilteredPortfolio, start_date: datetime.date, end_date: datetime.date) -> Series:
        """
        compare market value with cost value on every price or volume change

        Do not use cash value here, because cash value could be negative (e.g. sold stock with a loss).
        """
        values = portfolio_values(p, start_date, end_date)
        return [(value.date, compute_returns(value.cost, value.market)) for value in values]

    def rebase(self, base: float, series: Series) -> Series:
        # the returns metric computes cost vs market value for every day, i.e. it does not compound returns
        # therefore, offset the entire chart by the base value
        return [(date, value - base) for date, value in series]


def compute_returns(initial_value: Decimal, final_value: Decimal) -> float:
    if initial_value == ZERO:
        return 0.0
    return float((final_value - initial_value) / initial_value)

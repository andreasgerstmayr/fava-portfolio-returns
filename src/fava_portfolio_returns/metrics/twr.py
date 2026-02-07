import datetime
import itertools
import logging
import math
from typing import Generator

from beancount.core.number import ZERO

from fava_portfolio_returns.api.portfolio import portfolio_values
from fava_portfolio_returns.core.portfolio import FilteredPortfolio
from fava_portfolio_returns.metrics.base import MetricBase
from fava_portfolio_returns.metrics.base import Series

logger = logging.getLogger(__name__)


class TWR(MetricBase):
    """
    Time-Weighted Rate of Return

    Time-Weighted Return (TWR) eliminates the effects of cash flows.
    TWR includes all dividends and fees, i.e. the price of stock X won't match the TWR of a portfolio with a savings plan for X.
    """

    def single(self, p: FilteredPortfolio, start_date: datetime.date, end_date: datetime.date) -> float:
        return math.prod(returns for _date, returns in subperiod_returns(p, start_date, end_date)) - 1.0

    def series(self, p: FilteredPortfolio, start_date: datetime.date, end_date: datetime.date) -> Series:
        twr = 1.0
        twrs: Series = []
        for date, growth_factor in subperiod_returns(p, start_date, end_date):
            twr *= growth_factor
            twrs.append((date, twr - 1.0))
        return twrs

    def rebase(self, base: float, series: Series) -> Series:
        # TWR compounds returns
        return [(date, (value + 1.0) / (base + 1.0) - 1.0) for date, value in series]


# cashflow-adjusted portfolio growth factor, i.e. how does 1 USD grow over time, ignoring effects of cashflows
def subperiod_returns(
    p: FilteredPortfolio, start_date: datetime.date, end_date: datetime.date
) -> Generator[tuple[datetime.date, float], None, None]:
    values = portfolio_values(p, start_date, end_date)

    if values:
        yield (values[0].date, 1.0)

    for current, next_value in itertools.pairwise(values):
        # https://en.wikipedia.org/wiki/Time-weighted_return#Time-weighted_return_compensating_for_external_flows
        # portfolio is valued immediately after each external flow
        cashflow = next_value.cash - current.cash
        begin = current.market
        end = next_value.market - cashflow  # market value of next period excl. cashflow

        if begin == ZERO:
            continue

        returns = float(end) / float(begin)
        logger.debug(
            "Subperiod from %s to %s: begin=%.2f end=%.2f returns=%.2f%%",
            current.date,
            next_value.date,
            begin,
            end,
            returns - 1,
        )
        yield (next_value.date, returns)

import datetime
import logging
import math

from beancount.core.number import ZERO

from fava_portfolio_returns.api.portfolio import PortfolioValue
from fava_portfolio_returns.api.portfolio import portfolio_values
from fava_portfolio_returns.core.portfolio import FilteredPortfolio
from fava_portfolio_returns.returns.base import ReturnsBase
from fava_portfolio_returns.returns.base import Series

logger = logging.getLogger(__name__)


class TWR(ReturnsBase):
    """
    Time-Weighted Rate of Return

    Time-Weighted Return (TWR) eliminates the effects of cash flows.
    TWR includes all dividends and fees, i.e. the price of stock X won't match the TWR of a portfolio with a savings plan for X.
    """

    def single(self, p: FilteredPortfolio, start_date: datetime.date, end_date: datetime.date) -> float:
        values = portfolio_values(p, start_date, end_date)
        return math.prod(returns for _date, returns in _subperiods(values)) - 1.0

    def series(self, p: FilteredPortfolio, start_date: datetime.date, end_date: datetime.date) -> Series:
        values = portfolio_values(p, start_date, end_date)
        twrs: Series = []

        twr = 1.0
        for date, returns in _subperiods(values):
            twr *= returns
            twrs.append((date, twr - 1.0))

        return twrs

    def rebase(self, base: float, series: Series) -> Series:
        # TWR compounds returns
        return [(date, (value + 1.0) / (base + 1.0) - 1.0) for date, value in series]


# cashflow-adjusted portfolio growth factor, i.e. how does 1 USD grow over time, ignoring effects of cashflows
def _subperiods(values: list[PortfolioValue]):
    if values:
        yield values[0].date, 1.0

    for i in range(len(values) - 1):
        # https://en.wikipedia.org/wiki/Time-weighted_return#Time-weighted_return_compensating_for_external_flows
        # portfolio is valued immediately after each external flow
        begin = values[i].market
        if begin == ZERO:
            continue
        end = values[i + 1].market - (values[i + 1].cash - values[i].cash)  # next period, before cash flow

        returns = float(end) / float(begin)
        logger.debug(
            "Subperiod %d from %s to %s: begin=%.2f end=%.2f returns=%.2f%%",
            i,
            values[i].date,
            values[i + 1].date,
            begin,
            end,
            returns - 1,
        )
        yield (values[i + 1].date, returns)

import datetime
import logging

from beancount.core.number import ZERO

from fava_portfolio_returns.api.portfolio import PortfolioValue
from fava_portfolio_returns.api.portfolio import portfolio_values
from fava_portfolio_returns.core.portfolio import FilteredPortfolio
from fava_portfolio_returns.returns.base import ReturnsBase

logger = logging.getLogger(__name__)


class TWR(ReturnsBase):
    """
    Time-Weighted Rate of Return

    Time-Weighted Return (TWR) eliminates the effects of cash flows.
    TWR includes all dividends and fees, i.e. the price of stock X won't match the TWR of a portfolio with a savings plan for X.
    """

    def single(self, p: FilteredPortfolio, start_date: datetime.date, end_date: datetime.date) -> float:
        values = portfolio_values(p, start_date, end_date)
        return _twr(values)

    def series(
        self, p: FilteredPortfolio, start_date: datetime.date, end_date: datetime.date
    ) -> list[tuple[datetime.date, float]]:
        values = portfolio_values(p, start_date, end_date)
        return _twr(values, save_intermediate=True)


def _twr(values: list[PortfolioValue], save_intermediate=False):
    twrs: list[tuple[datetime.date, float]] = []
    if save_intermediate and values:
        twrs.append((values[0].date, 0.0))

    twr = 1.0
    for i in range(len(values) - 1):
        # https://en.wikipedia.org/wiki/Time-weighted_return#Time-weighted_return_compensating_for_external_flows
        # portfolio is valued immediately after each external flow
        begin = values[i].market
        if begin == ZERO:
            continue
        end = values[i + 1].market - (values[i + 1].cash - values[i].cash)  # next period, before cash flow

        returns = float(end) / float(begin)
        twr *= returns

        if save_intermediate:
            twrs.append((values[i + 1].date, twr - 1))

        logger.debug(
            "Subperiod %d from %s to %s: begin=%.2f end=%.2f returns=%.2f%%",
            i,
            values[i].date,
            values[i + 1].date,
            begin,
            end,
            returns - 1,
        )

    return twrs if save_intermediate else (twr - 1)

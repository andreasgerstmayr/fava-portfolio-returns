import datetime
import logging

from fava_portfolio_returns.api.portfolio import portfolio_values
from fava_portfolio_returns.core.intervals import ONE_DAY
from fava_portfolio_returns.core.portfolio import FilteredPortfolio
from fava_portfolio_returns.core.utils import market_value_of_inv
from fava_portfolio_returns.returns.base import ReturnsBase

logger = logging.getLogger(__name__)


class MonetaryReturns(ReturnsBase):
    """Return compares the market value with the invested capital"""

    def single(self, p: FilteredPortfolio, start_date: datetime.date, end_date: datetime.date) -> float:
        """calculates the difference between the gains before and after the time frame"""
        # Use the day before start_date, to compare the returns before the selected interval with the end of the selected interval.
        # For example, January has a single price directive, and we want to get the returns for January.
        # We need to compare the values *before* January with values at the end of January.
        start_balance = p.balance_at(start_date - ONE_DAY)
        start_market = market_value_of_inv(
            p.pricer, p.target_currency, start_balance, start_date - ONE_DAY, record=True
        )
        start_cash = p.cash_at(start_date - ONE_DAY)

        end_balance = p.balance_at(end_date)
        end_market = market_value_of_inv(p.pricer, p.target_currency, end_balance, end_date, record=True)
        end_cash = p.cash_at(end_date)

        start_returns = start_market - start_cash
        end_returns = end_market - end_cash
        return float(end_returns - start_returns)

    def series(
        self, p: FilteredPortfolio, start_date: datetime.date, end_date: datetime.date
    ) -> list[tuple[datetime.date, float]]:
        """compare market value with invested capital on every price or volume change"""
        values = portfolio_values(p, start_date, end_date)
        return [(value.date, float(value.market - value.cash)) for value in values]

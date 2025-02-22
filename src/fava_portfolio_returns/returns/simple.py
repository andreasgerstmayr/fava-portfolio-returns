import datetime
import logging

from fava_portfolio_returns.api.portfolio import portfolio_values
from fava_portfolio_returns.core.portfolio import FilteredPortfolio
from fava_portfolio_returns.returns.base import ReturnsBase
from fava_portfolio_returns.returns.returns import compute_returns

logger = logging.getLogger(__name__)


class SimpleReturns(ReturnsBase):
    """
    Return compares the market value with the cost value

    single() is not implemented, because it doesn't make sense in some cases:
    * comparing market value with cash_in-cash_out: cash_in-cash_out can be negative at a specific date, but we still own stocks
    * comparing market value with cash_in: deposit X, withdraw Y, comparing X with market value Z doesn't make sense
    """

    def series(
        self, p: FilteredPortfolio, start_date: datetime.date, end_date: datetime.date
    ) -> list[tuple[datetime.date, float]]:
        """
        compare market value with cost value on every price or volume change

        Do not use cash value here, because cash value could be negative (e.g. sold stock with a loss).
        """
        values = portfolio_values(p, start_date, end_date)
        return [(value.date, compute_returns(value.cost, value.market)) for value in values]

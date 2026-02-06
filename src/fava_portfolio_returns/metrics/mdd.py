import datetime
import logging

from fava_portfolio_returns.core.portfolio import FilteredPortfolio
from fava_portfolio_returns.metrics.base import MetricBase
from fava_portfolio_returns.metrics.base import Series
from fava_portfolio_returns.metrics.twr import TWR

logger = logging.getLogger(__name__)


class MDD(MetricBase):
    """
    Maximum Drawdown (MDD)

    Maximum Drawdown computes the maximum decline from a historical peak.
    It is based on the TWR to eliminate the effects of cash flows.
    """

    def single(self, p: FilteredPortfolio, start_date: datetime.date, end_date: datetime.date) -> float:
        drawdowns = self.series(p, start_date, end_date)
        return min((v for _, v in drawdowns), default=0.0)

    def series(self, p: FilteredPortfolio, start_date: datetime.date, end_date: datetime.date) -> Series:
        twr_series = TWR().series(p, start_date, end_date)

        drawdowns: Series = []
        peak = 1.0
        for date, twr in twr_series:
            wealth_index = 1.0 + twr
            peak = max(peak, wealth_index)
            drawdown = (wealth_index - peak) / peak
            logger.debug("MDD: date=%s wealth_index=%.2f peak=%.2f drawdown=%.2f", date, wealth_index, peak, drawdown)
            drawdowns.append((date, drawdown))

        return drawdowns

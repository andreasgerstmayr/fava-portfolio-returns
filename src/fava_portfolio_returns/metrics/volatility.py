import datetime
import itertools
import math
import statistics

from fava_portfolio_returns.core.portfolio import FilteredPortfolio
from fava_portfolio_returns.metrics.base import MetricBase
from fava_portfolio_returns.metrics.twr import subperiod_returns


class Volatility(MetricBase):
    """
    Volatility

    Annualized volatility, based on TWR period returns.
    """

    def single(self, p: FilteredPortfolio, start_date: datetime.date, end_date: datetime.date) -> float:
        periods = list(subperiod_returns(p, start_date, end_date))
        intervals = [
            ((date - prev_date).days, growth_factor - 1.0)
            for (prev_date, _), (date, growth_factor) in itertools.pairwise(periods)
        ]

        if len(intervals) < 2:
            return 0.0

        volatility = statistics.stdev(period_return for _, period_return in intervals)
        avg_period_years = 365.0 / statistics.fmean(days for days, _ in intervals)
        return volatility * math.sqrt(avg_period_years)

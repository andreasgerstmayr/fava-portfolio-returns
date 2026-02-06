import abc
import datetime

from fava_portfolio_returns._vendor.beangrow.reports import Interval
from fava_portfolio_returns.core.portfolio import FilteredPortfolio

Series = list[tuple[datetime.date, float]]


class MetricBase(abc.ABC):
    def single(self, p: FilteredPortfolio, start_date: datetime.date, end_date: datetime.date) -> float:
        raise NotImplementedError("single() is not implemented for this metric")

    def series(self, p: FilteredPortfolio, start_date: datetime.date, end_date: datetime.date) -> Series:
        raise NotImplementedError("series() is not implemented for this metric")

    def rebase(self, base: float, series: Series) -> Series:
        """rebase series to align them at 0; useful when comparing multiple series"""
        raise NotImplementedError("rebase() is not implemented for this metric")

    def intervals(self, p: FilteredPortfolio, intervals: list[Interval]) -> list[tuple[str, float]]:
        return [
            (interval_name, self.single(p, start_date, end_date)) for interval_name, start_date, end_date in intervals
        ]

    def rolling_window(
        self, p: FilteredPortfolio, start_date: datetime.date, end_date: datetime.date, window_days=365, max_points=50
    ) -> Series:
        window_delta = datetime.timedelta(days=window_days)

        cash_flows = p.cash_flows()
        if cash_flows and start_date - window_delta < cash_flows[0].date:
            # make sure window starts after first cash flow
            start_date = cash_flows[0].date + window_delta

        num_days = (end_date - start_date).days
        step = max(num_days // max_points, 1)
        dates = (start_date + datetime.timedelta(n) for n in range(0, num_days, step))
        return [(date, self.single(p, date - window_delta, date)) for date in dates]

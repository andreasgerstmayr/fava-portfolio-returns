import abc
import datetime

from fava_portfolio_returns._vendor.beangrow.reports import Interval
from fava_portfolio_returns.core.portfolio import FilteredPortfolio


class ReturnsBase(abc.ABC):
    def single(self, p: FilteredPortfolio, start_date: datetime.date, end_date: datetime.date) -> float:
        raise NotImplementedError("single() is not implemented for this method of calculating portfolio returns")

    def series(
        self, p: FilteredPortfolio, start_date: datetime.date, end_date: datetime.date
    ) -> list[tuple[datetime.date, float]]:
        raise NotImplementedError("series() is not implemented for this method of calculating portfolio returns")

    def intervals(self, p: FilteredPortfolio, intervals: list[Interval]) -> list[tuple[str, float]]:
        ret = []
        for interval_name, date_start, date_end in intervals:
            returns = self.single(p, date_start, date_end)
            ret.append((interval_name, returns))
        return ret

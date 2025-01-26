import abc
import datetime
from decimal import Decimal

from beangrow.investments import AccountData
from beangrow.reports import Interval
from beangrow.returns import Pricer


class ReturnsBase(abc.ABC):
    def single(
        self,
        pricer: Pricer,
        account_data_list: list[AccountData],
        target_currency: str,
        start_date: datetime.date,
        end_date: datetime.date,
    ) -> Decimal:
        raise NotImplementedError("single() is not implemented for this method of calculating portfolio returns")

    def series(
        self,
        pricer: Pricer,
        account_data_list: list[AccountData],
        target_currency: str,
        start_date: datetime.date,
        end_date: datetime.date,
    ):
        raise NotImplementedError("series() is not implemented for this method of calculating portfolio returns")

    def intervals(
        self,
        pricer: Pricer,
        account_data_list: list[AccountData],
        target_currency: str,
        intervals: list[Interval],
    ):
        ret = []
        for interval_name, date_start, date_end in intervals:
            returns = self.single(pricer, account_data_list, target_currency, date_start, date_end)
            ret.append([interval_name, returns])
        return ret

import datetime

import beangrow.returns as returnslib
from beangrow.investments import AccountData

from fava_portfolio_returns.api.cash_flows import convert_cash_flows_to_currency
from fava_portfolio_returns.core.intervals import ONE_DAY
from fava_portfolio_returns.returns.base import ReturnsBase


class IRR(ReturnsBase):
    """Internal Rate of Return"""

    def single(
        self,
        pricer: returnslib.Pricer,
        account_data_list: list[AccountData],
        target_currency: str,
        start_date: datetime.date,
        end_date: datetime.date,
    ):
        cash_flows = returnslib.truncate_and_merge_cash_flows(pricer, account_data_list, start_date, end_date + ONE_DAY)
        cash_flows = convert_cash_flows_to_currency(pricer, target_currency, cash_flows)
        return returnslib.compute_irr(cash_flows, pricer, target_currency, end_date + ONE_DAY)

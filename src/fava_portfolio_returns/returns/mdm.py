import datetime

from fava_portfolio_returns._vendor.beangrow.returns import compute_dietz
from fava_portfolio_returns._vendor.beangrow.returns import truncate_and_merge_cash_flows
from fava_portfolio_returns.api.cash_flows import convert_cash_flows_to_currency
from fava_portfolio_returns.core.intervals import ONE_DAY
from fava_portfolio_returns.core.portfolio import FilteredPortfolio
from fava_portfolio_returns.returns.base import ReturnsBase


class ModifiedDietzMethod(ReturnsBase):
    """
    Modified Dietz Method

    Modified Dietz Method (MDM) accounts for the timing and magnitude of cash flows.
    """

    def single(self, p: FilteredPortfolio, start_date: datetime.date, end_date: datetime.date) -> float:
        # in beangrow the end date is exclusive, therefore add one day
        cash_flows = truncate_and_merge_cash_flows(p.pricer, p.account_data_list, start_date, end_date + ONE_DAY)
        cash_flows = convert_cash_flows_to_currency(p.pricer, p.target_currency, cash_flows)
        return compute_dietz(cash_flows, p.pricer, p.target_currency, end_date + ONE_DAY)

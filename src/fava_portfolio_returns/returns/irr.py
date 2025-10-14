import datetime
import logging

from fava_portfolio_returns._vendor.beangrow.returns import compute_irr
from fava_portfolio_returns._vendor.beangrow.returns import truncate_and_merge_cash_flows
from fava_portfolio_returns.api.cash_flows import convert_cash_flows_to_currency
from fava_portfolio_returns.core.intervals import ONE_DAY
from fava_portfolio_returns.core.portfolio import FilteredPortfolio
from fava_portfolio_returns.returns.base import ReturnsBase

logger = logging.getLogger(__name__)


class IRR(ReturnsBase):
    """
    Internal Rate of Return

    Internal Rate of Return (IRR) accounts for the timing and magnitude of cash flows.
    """

    def single(self, p: FilteredPortfolio, start_date: datetime.date, end_date: datetime.date) -> float:
        # in beangrow the end date is exclusive, therefore add one day
        cash_flows = truncate_and_merge_cash_flows(p.pricer, p.account_data_list, start_date, end_date + ONE_DAY)
        cash_flows = convert_cash_flows_to_currency(p.pricer, p.target_currency, cash_flows)

        if logger.isEnabledFor(logging.DEBUG):
            parts = []
            for flow in cash_flows:
                years = (end_date - flow.date).days / 365
                parts.append(f"{-(flow.amount.number or 0):.2f}*(1+x)^{years:.2f}")
            logger.debug("Calculating IRR from %s to %s: %s = 0", start_date, end_date, " + ".join(parts))

        return compute_irr(cash_flows, p.pricer, p.target_currency, end_date + ONE_DAY)

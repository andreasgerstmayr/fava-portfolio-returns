import datetime
import logging
from decimal import Decimal

from beancount.core import convert

from fava_portfolio_returns.core.portfolio import FilteredPortfolio
from fava_portfolio_returns.core.portfolio import Portfolio
from fava_portfolio_returns.core.utils import cost_value_of_inv
from fava_portfolio_returns.core.utils import market_value_of_inv
from fava_portfolio_returns.returns.irr import IRR
from fava_portfolio_returns.returns.mdm import ModifiedDietzMethod
from fava_portfolio_returns.returns.monetary import MonetaryReturns
from fava_portfolio_returns.returns.twr import TWR

logger = logging.getLogger(__name__)


def group_stats(p: FilteredPortfolio, start_date: datetime.date, end_date: datetime.date):
    balance = p.balance_at(end_date)
    cost_value = cost_value_of_inv(p.pricer, p.target_currency, balance)
    market_value = market_value_of_inv(p.pricer, p.target_currency, balance, end_date, record=True)
    # reduce to units (i.e. removing cost attribute) after calculating market value, because convert.get_value() only works with positions held at cost
    # this will convert for example CORP -> USD (cost currency) -> EUR (target currency), instead of CORP -> EUR.
    # see https://github.com/andreasgerstmayr/fava-portfolio-returns/issues/53
    units = balance.reduce(convert.get_units)  # sums 1 CORP {} + 2 CORP {} => 3 CORP

    total_pnl = Decimal(MonetaryReturns().single(p, start_date, end_date))
    unrealized_pnl = market_value - cost_value
    realized_pnl = total_pnl - unrealized_pnl
    irr = IRR().single(p, start_date, end_date)
    mdm = ModifiedDietzMethod().single(p, start_date, end_date)
    twr = TWR().single(p, start_date, end_date)
    return {
        "units": [pos.units for pos in units],
        "costValue": cost_value,
        "marketValue": market_value,
        "totalPnl": total_pnl,
        "realizedPnl": realized_pnl,
        "unrealizedPnl": unrealized_pnl,
        "irr": irr,
        "mdm": mdm,
        "twr": twr,
    }


def investments_group_by_group(p: Portfolio, start_date: datetime.date, end_date: datetime.date):
    for group in p.investments_config.groups:
        logger.debug("calculating stats for %s", group.name)
        fp = p.filter([group.id], group.currency)
        yield {
            "id": group.id,
            "name": group.name,
            "currency": fp.target_currency,
            **group_stats(fp, start_date, end_date),
        }


def investments_group_by_currency(
    p: Portfolio, target_currency: str, start_date: datetime.date, end_date: datetime.date
):
    for currency in p.investments_config.currencies:
        logger.debug("calculating stats for %s", currency.name)
        fp = p.filter([currency.id], target_currency)
        yield {
            "id": currency.id,
            "name": currency.name,
            "currency": fp.target_currency,
            **group_stats(fp, start_date, end_date),
        }

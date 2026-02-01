import datetime
import logging
import math
from decimal import Decimal

import numpy as np
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


def _sanitize_float(value):
    """Replace inf/nan with None so the value is JSON-serializable."""
    if isinstance(value, (float, np.floating)):
        if math.isinf(value) or math.isnan(value):
            return None
    return value


def group_stats(p: FilteredPortfolio, start_date: datetime.date, end_date: datetime.date):
    balance = p.balance_at(end_date)
    cost_value = cost_value_of_inv(p.pricer, p.target_currency, balance)
    market_value = market_value_of_inv(p.pricer, p.target_currency, balance, end_date)
    # reduce to units (i.e. removing cost attribute) after calculating market value, because convert.get_value() only works with positions held at cost
    # this will convert for example CORP -> USD (cost currency) -> EUR (target currency), instead of CORP -> EUR.
    # see https://github.com/andreasgerstmayr/fava-portfolio-returns/issues/53
    units = balance.reduce(convert.get_units)  # sums 1 CORP {} + 2 CORP {} => 3 CORP

    total_pnl = Decimal(MonetaryReturns().single(p, start_date, end_date))
    # Period-bounded unrealized P&L: change in unrealized gains during the period
    # Use start_date - 1 day to align with MonetaryReturns' convention
    one_day = datetime.timedelta(days=1)
    unrealized_pnl_end = market_value - cost_value
    start_balance = p.balance_at(start_date - one_day)
    start_cost_value = cost_value_of_inv(p.pricer, p.target_currency, start_balance)
    start_market_value = market_value_of_inv(p.pricer, p.target_currency, start_balance, start_date - one_day)
    unrealized_pnl_start = start_market_value - start_cost_value
    unrealized_pnl = unrealized_pnl_end - unrealized_pnl_start
    realized_pnl = total_pnl - unrealized_pnl
    irr = _sanitize_float(IRR().single(p, start_date, end_date))
    mdm = _sanitize_float(ModifiedDietzMethod().single(p, start_date, end_date))
    twr = _sanitize_float(TWR().single(p, start_date, end_date))
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

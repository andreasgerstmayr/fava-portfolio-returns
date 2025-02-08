import datetime
import logging

from beancount.core import convert

from fava_portfolio_returns.api.portfolio import portfolio_cash
from fava_portfolio_returns.core.portfolio import FilteredPortfolio
from fava_portfolio_returns.core.portfolio import Portfolio
from fava_portfolio_returns.core.utils import market_value_of_inv
from fava_portfolio_returns.returns.irr import IRR
from fava_portfolio_returns.returns.mdm import ModifiedDietzMethod
from fava_portfolio_returns.returns.monetary import MonetaryReturns
from fava_portfolio_returns.returns.twr import TWR

logger = logging.getLogger(__name__)


def group_stats(p: FilteredPortfolio, start_date: datetime.date, end_date: datetime.date):
    cash_in, cash_out = portfolio_cash(p, start_date, end_date)
    balance = p.balance_at(end_date)
    market_value = market_value_of_inv(p.pricer, p.target_currency, balance, end_date, record=True)
    # reduce to units (i.e. removing cost attribute) after calculating market value, because convert.get_value() only works with positions held at cost
    # this will convert for example CORP -> USD (cost currency) -> EUR (target currency), instead of CORP -> EUR.
    # see https://github.com/andreasgerstmayr/fava-portfolio-returns/issues/53
    balance = balance.reduce(convert.get_units)  # sums 1 CORP {} + 2 CORP {} => 3 CORP

    gains = MonetaryReturns().single(p, start_date, end_date)
    irr = IRR().single(p, start_date, end_date)
    mdm = ModifiedDietzMethod().single(p, start_date, end_date)
    twr = TWR().single(p, start_date, end_date)
    return {
        "units": [pos.units for pos in balance],
        "cashIn": cash_in,
        "cashOut": cash_out,
        "marketValue": market_value,
        "gains": gains,
        "irr": irr,
        "mdm": mdm,
        "twr": twr,
    }


def investments_group_by_group(p: Portfolio, start_date: datetime.date, end_date: datetime.date):
    for group in p.investment_groups.groups:
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
    for currency in p.investment_groups.currencies:
        logger.debug("calculating stats for %s", currency.name)
        fp = p.filter([currency.id], target_currency)
        yield {
            "id": currency.id,
            "name": currency.name,
            "currency": target_currency,
            **group_stats(fp, start_date, end_date),
        }

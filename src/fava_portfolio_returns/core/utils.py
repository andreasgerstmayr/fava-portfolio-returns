import datetime
from decimal import Decimal
from typing import Optional

from beancount.core import convert
from beancount.core import prices
from beancount.core.inventory import Inventory
from beancount.core.number import ZERO
from fava.helpers import FavaAPIError

from fava_portfolio_returns._vendor.beangrow.investments import CashFlow
from fava_portfolio_returns._vendor.beangrow.returns import Pricer


class CurrencyConversionException(FavaAPIError):
    def __init__(self, source: str, target: str, date: Optional[datetime.date] = None):
        date = date or datetime.date.today()
        super().__init__(
            f"Could not convert {source} to {target} on {date}."
            f" Please add a price directive '{date} price {source} <conversion_rate> {target}' to your ledger."
        )


def cost_value_of_inv(pricer: Pricer, target_currency: str, balance: Inventory) -> Decimal:
    cost_balance = balance.reduce(convert.get_cost)
    return inv_to_currency(pricer, target_currency, cost_balance)


def market_value_of_inv(
    pricer: Pricer, target_currency: str, balance: Inventory, date: datetime.date, record=False
) -> Decimal:
    # first, get market value of all position in cost currency
    if record:
        # record requested currency/date in pricer.required_prices (for "Missing Prices" page)
        value_balance = balance.reduce(pricer.get_value, date)
    else:
        value_balance = balance.reduce(convert.get_value, pricer.price_map, date)

    # then convert to target currency
    return inv_to_currency(pricer, target_currency, value_balance)


def inv_to_currency(
    pricer: Pricer, target_currency: str, inventory: Inventory, date: Optional[datetime.date] = None
) -> Decimal:
    cost_balance = inventory.reduce(convert.convert_position, target_currency, pricer.price_map, date)
    pos = cost_balance.get_only_position()
    if pos and pos.units.currency != target_currency:
        raise CurrencyConversionException(pos.units.currency, target_currency, date)
    return pos.units.number if pos else ZERO


def convert_cash_flows_to_currency(pricer: Pricer, target_currency: str, flows: list[CashFlow]) -> list[CashFlow]:
    target_flows = []
    for flow in flows:
        target_amt = pricer.convert_amount(flow.amount, target_currency, flow.date)
        if target_amt.currency != target_currency:
            raise CurrencyConversionException(target_amt.currency, target_currency, flow.date)

        target_flow = flow._replace(amount=target_amt)
        target_flows.append(target_flow)
    return target_flows


def filter_cash_flows_by_date(
    cash_flows: list[CashFlow], start_date: datetime.date, end_date: datetime.date
) -> list[CashFlow]:
    return [flow for flow in cash_flows if start_date <= flow.date <= end_date]


def get_prices(pricer: Pricer, source: str, target: str) -> list[tuple[datetime.date, Decimal]]:
    """
    :param tuple pair:  (currency, target_currency), e.g. (CORP, USD)
    """
    try:
        return prices.get_all_prices(pricer.price_map, (source, target))
    except KeyError:
        raise CurrencyConversionException(source=source, target=target)

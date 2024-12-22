import datetime
from collections import defaultdict
from decimal import Decimal

import beangrow.returns as returnslib
from beancount.core import convert
from beancount.core.inventory import Inventory
from beancount.core.number import ZERO
from beancount.core.position import Position
from beangrow.investments import AccountData, CashFlow, Cat
from fava.helpers import FavaAPIError


class CurrencyConversionException(FavaAPIError):
    def __init__(self, source, target, date):
        super().__init__(
            f"Could not convert {source} to {target} on {date}."
            f" Please add a price directive '{date} price {source} <conversion_rate> {target}' to your ledger."
        )


def get_cost_value_of_inventory(pricer: returnslib.Pricer, target_currency: str, balance: Inventory) -> Decimal:
    cost_balance = balance.reduce(convert.get_cost)
    target_ccy_balance = cost_balance.reduce(convert.convert_position, target_currency, pricer.price_map)
    pos: Position | None = target_ccy_balance.get_only_position()
    if pos and pos.units.currency != target_currency:
        raise CurrencyConversionException(pos.units.currency, target_currency, "today")
    return pos.units.number if pos and pos.units.number is not None else ZERO


def get_market_value_of_inventory(
    pricer: returnslib.Pricer, target_currency: str, balance: Inventory, date: datetime.date
) -> Decimal:
    # get market value in the cost currency of the positions
    value_balance = balance.reduce(convert.get_value, pricer.price_map, date)
    # convert to target currency
    target_ccy_balance = value_balance.reduce(convert.convert_position, target_currency, pricer.price_map, date)
    pos: Position | None = target_ccy_balance.get_only_position()
    if pos and pos.units.currency != target_currency:
        raise CurrencyConversionException(pos.units.currency, target_currency, date)
    return pos.units.number if pos and pos.units.number is not None else ZERO


def convert_cash_flows_to_currency(
    pricer: returnslib.Pricer, target_currency: str, flows: list[CashFlow]
) -> list[CashFlow]:
    target_flows = []
    for flow in flows:
        target_amt = pricer.convert_amount(flow.amount, target_currency, flow.date)
        if target_amt.currency != target_currency:
            raise CurrencyConversionException(target_amt.currency, target_currency, flow.date)

        target_flow = flow._replace(amount=target_amt)
        target_flows.append(target_flow)
    return target_flows


def get_cash_flows_time_range(account_data_list: list[AccountData], only_dividends=False):
    start_date = None
    end_date = None

    for account_data in account_data_list:
        for flow in account_data.cash_flows:
            if only_dividends and not flow.is_dividend:
                continue

            if not start_date or flow.date < start_date:
                start_date = flow.date
            if not end_date or flow.date > end_date:
                end_date = flow.date

    return start_date, end_date


def compute_balance_at(account_data_list: list[AccountData], date: datetime.date) -> Inventory:
    balance = Inventory()
    for account_data in account_data_list:
        for entry in account_data.transactions:
            if entry.date > date:
                break
            for posting in entry.postings:
                if posting.meta["category"] is Cat.ASSET:
                    balance.add_position(posting)
    return balance


def merge_cash_flows(account_data_list: list[AccountData]) -> list[CashFlow]:
    cash_flows: list[CashFlow] = []
    for account_data in account_data_list:
        cash_flows.extend(account_data.cash_flows)
    cash_flows.sort(key=lambda flow: flow.date)
    return cash_flows


def filter_cash_flows_by_date(
    cash_flows: list[CashFlow], start_date: datetime.date, end_date: datetime.date
) -> list[CashFlow]:
    return [flow for flow in cash_flows if start_date <= flow.date <= end_date]


def group_cash_flows_by_date(cash_flows: list[CashFlow]) -> list[tuple[datetime.date, Decimal]]:
    flows_by_date: dict[datetime.date, Decimal] = defaultdict(Decimal)
    for flow in cash_flows:
        flows_by_date[flow.date] += flow.amount.number
    return sorted(flows_by_date.items(), key=lambda x: x[0])

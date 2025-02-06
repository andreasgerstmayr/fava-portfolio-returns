import datetime
import itertools
import typing
from collections import defaultdict
from decimal import Decimal

from beancount.core import convert, data
from beancount.core.data import Transaction
from beancount.core.inventory import Inventory
from beancount.core.number import ZERO
from beangrow.investments import AccountData, Cat
from beangrow.returns import Pricer, compute_portfolio_values

from fava_portfolio_returns.api.cash_flows import convert_cash_flows_to_currency
from fava_portfolio_returns.core.utils import (
    compute_balance_at,
    get_cash_flows_time_range,
    get_cost_value_of_inventory,
    get_market_value_of_inventory,
    merge_cash_flows,
)
from fava_portfolio_returns.returns.returns import compute_annualized_returns, compute_returns


def portfolio_allocation(
    pricer: Pricer, account_data_list: list[AccountData], target_currency: str, end_date: datetime.date
):
    market_values: dict[tuple, Decimal] = defaultdict(Decimal)
    for account in account_data_list:
        commodity = account.commodity.meta.get("name", account.commodity.currency)
        currency = account.currency
        market_value = get_market_value_of_inventory(pricer, target_currency, account.balance, end_date)
        market_values[(currency, commodity)] += market_value

    allocation = [
        {
            "currency": currency,
            "commodity": commodity,
            "marketValue": market_value,
        }
        for (currency, commodity), market_value in market_values.items()
    ]
    allocation.sort(key=lambda x: x["marketValue"], reverse=True)

    return allocation


def portolio_summary(
    pricer: Pricer, account_data_list: list[AccountData], target_currency: str, end_date: datetime.date
):
    cash_in = ZERO  # all incoming cash in target currency
    cash_out = ZERO  # all outgoing cash in target currency

    cash_flows = merge_cash_flows(account_data_list)
    cash_flows = [flow for flow in cash_flows if flow.date <= end_date]
    cash_flows = convert_cash_flows_to_currency(pricer, target_currency, cash_flows)
    for flow in cash_flows:
        if flow.amount.number >= 0:
            cash_out += flow.amount.number
        else:
            cash_in -= flow.amount.number

    balance = compute_balance_at(account_data_list, end_date)
    balance = balance.reduce(convert.get_units)

    market_value = get_market_value_of_inventory(pricer, target_currency, balance, end_date)

    returns_abs = (market_value + cash_out) - cash_in
    if market_value == ZERO:
        # commodity got sold
        returns_pct = compute_returns(cash_in, cash_out)
    else:
        returns_pct = compute_returns(cash_in - cash_out, market_value)

    dates = [flow.date for flow in cash_flows]
    if dates:
        years = Decimal((max(dates) - min(dates)).days + 1) / 365
        returns_pct_annualized = compute_annualized_returns(returns_pct, years)
    else:
        returns_pct_annualized = 0

    return balance, cash_in, cash_out, market_value, returns_abs, returns_pct, returns_pct_annualized


def portfolio_market_values(
    pricer: Pricer,
    account_data_list: list[AccountData],
    target_currency: str,
    start_date: datetime.date,
    end_date: datetime.date,
):
    transactions = data.sorted([txn for ad in account_data_list for txn in ad.transactions])
    value_dates, value_values = compute_portfolio_values(pricer.price_map, target_currency, transactions)
    series = list(zip(value_dates, value_values))

    cf_start, _ = get_cash_flows_time_range(account_data_list)
    # before the first cash flow, the market value is always 0. skip these items.
    # do not skip items after the last cash flow
    start_date = max(start_date, cf_start) if cf_start else start_date
    series = [(date, value) for date, value in series if start_date <= date <= end_date]

    return series


def portfolio_cost_values(
    pricer: Pricer,
    account_data_list: list[AccountData],
    target_currency: str,
    start_date: datetime.date,
    end_date: datetime.date,
):
    series: list[tuple[datetime.date, Decimal]] = []
    initial_balance = Inventory()  # balance before start_date
    balance = Inventory()

    # sort transactions by date before using groupby()
    # ignore transactions after end_date
    _transactions = data.sorted([txn for ad in account_data_list for txn in ad.transactions if txn.date <= end_date])
    transactions = typing.cast(list[Transaction], _transactions)

    for date, group in itertools.groupby(transactions, key=lambda x: x.date):
        # iterate over transactions on the same day
        for entry in group:
            for posting in entry.postings:
                if posting.meta and posting.meta["category"] is Cat.ASSET:
                    balance.add_position(posting)
                    if date < start_date:
                        initial_balance.add_position(posting)

        if date >= start_date:
            value = get_cost_value_of_inventory(pricer, target_currency, balance)
            series.append((date, value))

    # insert the cumulative balance before start_date (if any)
    if not initial_balance.is_empty():
        value = get_cost_value_of_inventory(pricer, target_currency, initial_balance)
        series.insert(0, (start_date, value))

    return series

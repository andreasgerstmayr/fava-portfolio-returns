import datetime
from decimal import Decimal

import beangrow.returns as returnslib
from beancount.core.number import ZERO
from beangrow.investments import AccountData

from fava_portfolio_returns.core.utils import (
    convert_cash_flows_to_currency,
    filter_cash_flows_by_date,
    group_cash_flows_by_date,
    merge_cash_flows,
)


def cash_flows_list(
    pricer: returnslib.Pricer,
    account_data_list: list[AccountData],
    target_currency: str,
    start_date: datetime.date,
    end_date: datetime.date,
    dividends: bool,
):
    cash_flows = merge_cash_flows(account_data_list)
    cash_flows = filter_cash_flows_by_date(cash_flows, start_date, end_date)
    cash_flows = [flow for flow in cash_flows if flow.is_dividend == dividends]
    cash_flows = convert_cash_flows_to_currency(pricer, target_currency, cash_flows)
    return group_cash_flows_by_date(cash_flows)


def cash_flows_table(
    account_data_list: list[AccountData],
    start_date: datetime.date,
    end_date: datetime.date,
):
    cash_flows = merge_cash_flows(account_data_list)
    cash_flows = filter_cash_flows_by_date(cash_flows, start_date, end_date)
    return [
        {
            "date": flow.date,
            "amount": flow.amount,
            "isDividend": flow.is_dividend,
            "source": flow.source,
            "account": flow.account,
        }
        for flow in cash_flows
    ]


def cash_flows_cumulative(
    pricer: returnslib.Pricer,
    account_data_list: list[AccountData],
    target_currency: str,
    start_date: datetime.date,
    end_date: datetime.date,
):
    cash_flows = merge_cash_flows(account_data_list)
    cash_flows = convert_cash_flows_to_currency(pricer, target_currency, cash_flows)
    cash_flows_grouped = group_cash_flows_by_date(cash_flows)

    series: list[tuple[datetime.date, Decimal]] = []
    initial_value = ZERO  # cumulative value before start_date
    cumulative_value = ZERO
    for date, cost_value in cash_flows_grouped:
        cumulative_value += -cost_value
        if date < start_date:
            initial_value += -cost_value
        if start_date <= date <= end_date:
            series.append((date, cumulative_value))

    # add cumulative value before start_date
    if initial_value != ZERO:
        series.insert(0, (start_date, initial_value))

    return series

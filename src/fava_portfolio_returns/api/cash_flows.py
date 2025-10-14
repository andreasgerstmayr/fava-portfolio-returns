import datetime
from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal
from typing import Literal

from beancount.core.number import ZERO

from fava_portfolio_returns.core.intervals import interval_label
from fava_portfolio_returns.core.portfolio import FilteredPortfolio
from fava_portfolio_returns.core.utils import convert_cash_flows_to_currency
from fava_portfolio_returns.core.utils import filter_cash_flows_by_date


@dataclass
class CashFlowChartValue:
    date: str
    div: Decimal
    exdiv: Decimal


def cash_flows_chart(
    p: FilteredPortfolio, start_date: datetime.date, end_date: datetime.date, interval: Literal["monthly", "yearly"]
):
    cash_flows = p.cash_flows()
    cash_flows = filter_cash_flows_by_date(cash_flows, start_date, end_date)
    cash_flows = convert_cash_flows_to_currency(p.pricer, p.target_currency, cash_flows)

    labelfn = interval_label(interval)
    chart: dict[str, CashFlowChartValue] = {}
    for flow in cash_flows:
        label = labelfn(flow.date)
        if label not in chart:
            chart[label] = CashFlowChartValue(date=label, div=ZERO, exdiv=ZERO)

        if flow.is_dividend:
            chart[label].div += flow.amount.number or ZERO
        else:
            chart[label].exdiv += flow.amount.number or ZERO

    # only required if echarts axis is set to 'category' instead of 'time'
    # for label in interval_labels(interval, start_date, end_date):
    #    if label not in chart:
    #        chart[label] = CashFlowChartValue(date=label, div=ZERO, exdiv=ZERO)
    return sorted(chart.values(), key=lambda x: x.date)


def cash_flows_table(p: FilteredPortfolio, start_date: datetime.date, end_date: datetime.date):
    cash_flows = p.cash_flows()
    cash_flows = filter_cash_flows_by_date(cash_flows, start_date, end_date)
    cash_flows = sorted(cash_flows, key=lambda x: x.date, reverse=True)
    return [
        {
            "date": flow.date,
            "amount": flow.amount,
            "isDividend": flow.is_dividend,
            "source": flow.source,
            "account": flow.account,
            "transaction": f"{flow.transaction.payee or ''} {flow.transaction.narration or ''}".strip()
            if flow.transaction
            else "",
        }
        for flow in cash_flows
    ]


def dividends_chart(
    p: FilteredPortfolio,
    start_date: datetime.date,
    end_date: datetime.date,
    interval: Literal["monthly", "yearly"],
):
    cash_flows = p.cash_flows()
    cash_flows = filter_cash_flows_by_date(cash_flows, start_date, end_date)
    cash_flows = [flow for flow in cash_flows if flow.is_dividend]
    cash_flows = convert_cash_flows_to_currency(p.pricer, p.target_currency, cash_flows)

    currency_by_account = {acc.assetAccount: acc.currency for acc in p.portfolio.investments_config.accounts}
    currency_name_by_currency = {cur.currency: cur.name for cur in p.portfolio.investments_config.currencies}

    labelfn = interval_label(interval)
    chart: dict[str, dict[str, str | Decimal]] = {}
    for flow in cash_flows:
        label = labelfn(flow.date)
        currency = currency_by_account[flow.account]
        currency_name = currency_name_by_currency[currency]

        if label not in chart:
            chart[label] = defaultdict(Decimal)
            chart[label]["date"] = label
        chart[label][currency_name] += flow.amount.number  # type: ignore[operator]

    # only required if echarts axis is set to 'category' instead of 'time'
    # for label in interval_labels(interval, start_date, end_date):
    #    if label not in chart:
    #        chart[label] = {"date": label}
    return sorted(chart.values(), key=lambda x: x["date"])

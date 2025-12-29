import datetime
from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal
from typing import Literal

from beancount.core.number import ZERO

from fava_portfolio_returns.core.intervals import truncate_date_fn
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

    truncate_date = truncate_date_fn(interval)
    # ex. {"2025": {"date": "2025", "div": 5, "exdiv": 3}}
    chart: dict[str, CashFlowChartValue] = {}
    for flow in cash_flows:
        date = truncate_date(flow.date)
        if date not in chart:
            chart[date] = CashFlowChartValue(date=date, div=ZERO, exdiv=ZERO)

        if flow.is_dividend:
            chart[date].div += flow.amount.number or ZERO
        else:
            chart[date].exdiv += flow.amount.number or ZERO

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

    truncate_date = truncate_date_fn(interval)
    # ex. {"2025": {"date": "2025", "Investment1": 5, "Investment2": 3}}
    chart: dict[str, dict[str, str | Decimal]] = {}
    for flow in cash_flows:
        date = truncate_date(flow.date)
        currency = currency_by_account[flow.account]
        currency_name = currency_name_by_currency[currency]

        if date not in chart:
            chart[date] = defaultdict(Decimal)
            chart[date]["date"] = date
        chart[date][currency_name] += flow.amount.number  # type: ignore[operator]

    return sorted(chart.values(), key=lambda x: x["date"])

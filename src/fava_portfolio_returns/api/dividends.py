import datetime
from collections import defaultdict
from decimal import Decimal

from beangrow.investments import AccountData
from beangrow.returns import Pricer

from fava_portfolio_returns.api.cash_flows import convert_cash_flows_to_currency
from fava_portfolio_returns.core.portfolio import InvestmentGroups
from fava_portfolio_returns.core.utils import filter_cash_flows_by_date, merge_cash_flows

Date = datetime.date


def get_dividends(
    pricer: Pricer,
    investment_groups: InvestmentGroups,
    account_data_list: list[AccountData],
    target_currency: str,
    start_date: Date,
    end_date: Date,
    interval: str,
):
    cash_flows = merge_cash_flows(account_data_list)
    cash_flows = filter_cash_flows_by_date(cash_flows, start_date, end_date)
    cash_flows = [flow for flow in cash_flows if flow.is_dividend]
    cash_flows = convert_cash_flows_to_currency(pricer, target_currency, cash_flows)

    currency_by_account = {acc.assetAccount: acc.currency for acc in investment_groups.accounts}
    currency_name_by_currency = {cur.currency: cur.name for cur in investment_groups.currencies}

    dividends: dict[str, dict[str, Decimal]] = defaultdict(lambda: defaultdict(Decimal))
    for flow in cash_flows:
        currency = currency_by_account[flow.account]
        currency_name = currency_name_by_currency[currency]

        if interval == "monthly":
            key = f"{flow.date.month}/{flow.date.year}"
        else:
            key = f"{flow.date.year}"
        dividends[currency_name][key] += flow.amount.number
    return dividends

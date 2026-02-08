import datetime
import itertools
import logging
from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal

from fava_portfolio_returns.core.portfolio import FilteredPortfolio
from fava_portfolio_returns.core.utils import convert_cash_flows_to_currency
from fava_portfolio_returns.core.utils import filter_cash_flows_by_date
from fava_portfolio_returns.core.utils import get_prices
from fava_portfolio_returns.metrics.base import Series
from fava_portfolio_returns.metrics.registry import get_metric

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class NamedSeries:
    name: str
    data: Series
    cashFlows: Series  # pylint: disable=invalid-name


def get_series_cash_flows(fp: FilteredPortfolio, start_date: datetime.date, end_date: datetime.date):
    """Get filtered cash flows (excluding dividends)"""
    cash_flows = fp.cash_flows()
    cash_flows = filter_cash_flows_by_date(cash_flows, start_date, end_date)
    cash_flows = convert_cash_flows_to_currency(fp.pricer, fp.target_currency, cash_flows)

    # Aggregate by date, excluding dividends
    daily_flows: dict[datetime.date, Decimal] = defaultdict(Decimal)
    for flow in cash_flows:
        if not flow.is_dividend and flow.amount.number is not None:  # Exclude dividends and handle None values
            daily_flows[flow.date] += flow.amount.number

    return sorted(daily_flows.items(), key=lambda x: x[0])


def compare_chart(
    p: FilteredPortfolio, start_date: datetime.date, end_date: datetime.date, metric_name: str, compare_with: list[str]
):
    metric = get_metric(metric_name)
    returns = metric.series(p, start_date, end_date)
    cash_flows = get_series_cash_flows(p, start_date, end_date)
    returns_series: list[NamedSeries] = [NamedSeries(name="portfolio", data=returns, cashFlows=cash_flows)]

    for group in p.portfolio.investments_config.groups:
        if group.id in compare_with:
            fp = p.portfolio.filter([group.id], p.target_currency)
            returns_series.append(
                NamedSeries(
                    name=f"(GRP) {group.name}",
                    data=metric.series(fp, start_date, end_date),
                    cashFlows=get_series_cash_flows(fp, start_date, end_date),
                )
            )

    for account in p.portfolio.investments_config.accounts:
        if account.id in compare_with:
            fp = p.portfolio.filter([account.id], p.target_currency)
            returns_series.append(
                NamedSeries(
                    name=f"(ACC) {account.assetAccount}",
                    data=metric.series(fp, start_date, end_date),
                    cashFlows=get_series_cash_flows(fp, start_date, end_date),
                )
            )

    price_series: list[NamedSeries] = []
    for currency in p.portfolio.investments_config.currencies:
        if currency.id in compare_with:
            prices = get_prices(p.pricer, currency.currency, p.target_currency)
            prices_filtered = [(date, float(value)) for date, value in prices if start_date <= date <= end_date]
            price_series.append(
                NamedSeries(name=f"{currency.name} ({currency.currency})", data=prices_filtered, cashFlows=[])
            )

    # Find first common date of all series, which will be used as the base when rebasing the chart.
    all_dates = [frozenset(date for date, _ in serie.data) for serie in itertools.chain(returns_series, price_series)]
    for date in sorted(all_dates[0]):
        if all(date in dates for dates in all_dates[1:]):
            common_date = date
            break
    else:
        raise ValueError("No overlapping start date found for the selected series.")

    # cut off data before common date and rebase chart (align all series to start with 0% returns)
    series: list[NamedSeries] = []
    for serie in returns_series:
        truncated_series = truncate_series(serie.data, common_date)
        first_value = truncated_series[0][1]
        rebased_series = metric.rebase(first_value, truncated_series)
        truncated_cash_flows = truncate_cash_flows(serie.cashFlows, common_date)
        series.append(NamedSeries(name=serie.name, data=rebased_series, cashFlows=truncated_cash_flows))
    for serie in price_series:
        truncated_series = truncate_series(serie.data, common_date)
        first_price = truncated_series[0][1]
        rebased_series = [(date, value / first_price - 1.0) for date, value in truncated_series]
        series.append(NamedSeries(name=serie.name, data=rebased_series, cashFlows=[]))
    return series


def truncate_cash_flows(cash_flows: Series, start_date: datetime.date):
    """Truncate cash flow data, keep only after start_date"""
    result = []
    for flow_date, amount in cash_flows:
        if flow_date >= start_date:
            result.append((flow_date, amount))
    return result


def truncate_series(series: Series, start_date: datetime.date):
    for i, (date, _) in enumerate(series):
        if date == start_date:
            return series[i:]
    raise ValueError(f"Date {start_date} not found in series")

import datetime
import itertools
import logging
from dataclasses import dataclass

from fava_portfolio_returns.core.portfolio import FilteredPortfolio
from fava_portfolio_returns.core.utils import get_prices
from fava_portfolio_returns.returns.base import Series
from fava_portfolio_returns.returns.factory import RETURN_METHODS

logger = logging.getLogger(__name__)


@dataclass
class NamedSeries:
    name: str
    data: Series


def compare_chart(
    p: FilteredPortfolio, start_date: datetime.date, end_date: datetime.date, method: str, compare_with: list[str]
):
    returns_method = RETURN_METHODS.get(method)
    if not returns_method:
        raise ValueError(f"Invalid method '{method}'")

    returns = returns_method.series(p, start_date, end_date)
    returns_series: list[NamedSeries] = [NamedSeries(name="Returns", data=returns)]

    for group in p.portfolio.investments_config.groups:
        if group.id in compare_with:
            fp = p.portfolio.filter([group.id], p.target_currency)
            returns = returns_method.series(fp, start_date, end_date)
            returns_series.append(NamedSeries(name=f"(GRP) {group.name}", data=returns))

    for account in p.portfolio.investments_config.accounts:
        if account.id in compare_with:
            fp = p.portfolio.filter([account.id], p.target_currency)
            returns = returns_method.series(fp, start_date, end_date)
            returns_series.append(NamedSeries(name=f"(ACC) {account.assetAccount}", data=returns))

    price_series: list[NamedSeries] = []
    for currency in p.portfolio.investments_config.currencies:
        if currency.id in compare_with:
            prices = get_prices(p.pricer, currency.currency, p.target_currency)
            prices_filtered = [(date, float(value)) for date, value in prices if start_date <= date <= end_date]
            price_series.append(NamedSeries(name=f"{currency.name} ({currency.currency})", data=prices_filtered))

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
        cutoff = cutoff_series(serie.data, common_date)
        first_value = cutoff[0][1]
        rebased = returns_method.rebase(first_value, cutoff)
        series.append(NamedSeries(name=serie.name, data=rebased))
    for serie in price_series:
        cutoff = cutoff_series(serie.data, common_date)
        first_price = cutoff[0][1]
        rebased = [(date, value / first_price - 1.0) for date, value in cutoff]
        series.append(NamedSeries(name=serie.name, data=rebased))
    return series


def cutoff_series(series: Series, start_date: datetime.date):
    for i, (date, _) in enumerate(series):
        if date == start_date:
            return series[i:]
    raise ValueError(f"Date {start_date} not found in series")

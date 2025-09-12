import datetime
import logging
from dataclasses import dataclass
from typing import NamedTuple

from fava_portfolio_returns.core.portfolio import FilteredPortfolio
from fava_portfolio_returns.core.utils import get_prices
from fava_portfolio_returns.returns.factory import RETURN_METHODS

logger = logging.getLogger(__name__)


@dataclass
class DatedSeries:
    name: str
    dates: frozenset[datetime.date]
    data: list[tuple[datetime.date, float]]

    def __init__(self, name, data):
        self.name = name
        self.data = data
        self.dates = frozenset(date for date, _ in data)


class Series(NamedTuple):
    name: str
    data: list[tuple[datetime.date, float]]


def compare_chart(
    p: FilteredPortfolio, start_date: datetime.date, end_date: datetime.date, method: str, compare_with: list[str]
):
    returns_method = RETURN_METHODS.get(method)
    if not returns_method:
        raise ValueError(f"Invalid method {method}")

    group_series: list[DatedSeries] = [DatedSeries(name="Returns", data=returns_method.series(p, start_date, end_date))]
    for group in p.portfolio.investments_config.groups:
        if group.id in compare_with:
            fp = p.portfolio.filter([group.id], p.target_currency)
            group_series.append(
                DatedSeries(name=f"(GRP) {group.name}", data=returns_method.series(fp, start_date, end_date))
            )

    price_series: list[DatedSeries] = []
    for currency in p.portfolio.investments_config.currencies:
        if currency.id in compare_with:
            prices = get_prices(p.pricer, currency.currency, p.target_currency)
            prices_filtered = [(date, float(value)) for date, value in prices if start_date <= date <= end_date]
            price_series.append(DatedSeries(name=f"{currency.name} ({currency.currency})", data=prices_filtered))

    account_series: list[DatedSeries] = []
    for account in p.portfolio.investments_config.accounts:
        if account.id in compare_with:
            fp = p.portfolio.filter([account.id], p.target_currency)
            account_series.append(
                DatedSeries(name=f"(ACC) {account.assetAccount}", data=returns_method.series(fp, start_date, end_date))
            )

    # find first common date
    common_date = None
    for date in sorted(group_series[0].dates):
        if all(date in s.dates for s in group_series[1:]) and all(date in s.dates for s in price_series):
            common_date = date
            break
    else:
        raise ValueError("No overlapping start date found for the selected series.")

    # cut off data before common date
    for group_serie in group_series:
        for i, (date, _) in enumerate(group_serie.data):
            if date == common_date:
                group_serie.data = group_serie.data[i:]
                break
    for price_serie in price_series:
        for i, (date, _) in enumerate(price_serie.data):
            if date == common_date:
                price_serie.data = price_serie.data[i:]
                break
    for account_serie in account_series:
        for i, (date, _) in enumerate(account_serie.data):
            if date == common_date:
                account_serie.data = account_serie.data[i:]
                break

    # compute performance relative to first data point
    series: list[Series] = []
    for group_serie in group_series:
        first_return = group_serie.data[0][1]
        performance = [(date, returns - first_return) for date, returns in group_serie.data]
        series.append(Series(name=group_serie.name, data=performance))
    for price_serie in price_series:
        first_price = price_serie.data[0][1]
        performance = [(date, float(price / first_price - 1)) for date, price in price_serie.data]
        series.append(Series(name=price_serie.name, data=performance))
    for account_serie in account_series:
        first_return = account_serie.data[0][1]
        performance = [(date, returns - first_return) for date, returns in account_serie.data]
        series.append(Series(name=account_serie.name, data=performance))

    return series

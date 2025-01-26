import datetime
from collections import defaultdict
from decimal import Decimal

from beangrow.investments import AccountData
from beangrow.returns import Pricer

from fava_portfolio_returns.api.cash_flows import cash_flows_cumulative
from fava_portfolio_returns.api.portfolio import portfolio_cost_values, portfolio_market_values
from fava_portfolio_returns.returns.base import ReturnsBase
from fava_portfolio_returns.returns.returns import compute_returns


class SimpleReturns(ReturnsBase):
    """Returns"""

    def series(
        self,
        pricer: Pricer,
        account_data_list: list[AccountData],
        target_currency: str,
        start_date: datetime.date,
        end_date: datetime.date,
        percent=True,
    ):
        if percent:
            # when calculating the % returns, compare cost value with market value for every day
            # this does not include profits or losses of sold commodities
            # for example, when selling a stock at a loss, the cost value is 0
            cost_values = portfolio_cost_values(pricer, account_data_list, target_currency, start_date, end_date)
        else:
            # when calculating the absolute returns (profit and loss), compare the cumulative sum from the cash flows with the market value
            # this includes profits or losses of sold commodities
            # for example, when selling a stock at a loss, the cost value will be negative
            cost_values = cash_flows_cumulative(pricer, account_data_list, target_currency, start_date, end_date)

        cost_value_by_date: dict[datetime.date, Decimal] = defaultdict(Decimal)
        for date, value in cost_values:
            cost_value_by_date[date] = value

        market_values = portfolio_market_values(pricer, account_data_list, target_currency, start_date, end_date)
        market_value_by_date: dict[datetime.date, Decimal] = defaultdict(Decimal)
        for date, value in market_values:
            market_value_by_date[date] = value

        dates = set(list(cost_value_by_date.keys()) + list(market_value_by_date.keys()))

        latest_cost_value = None
        latest_market_value = None
        series: list[tuple[datetime.date, Decimal]] = []
        for date in sorted(dates):
            if date in cost_value_by_date:
                latest_cost_value = cost_value_by_date[date]
            if date in market_value_by_date:
                latest_market_value = market_value_by_date[date]

            if latest_cost_value is None or latest_market_value is None:
                # skip comparison if cost or market is undefined
                continue

            if percent:
                series.append((date, compute_returns(latest_cost_value, latest_market_value)))
            else:
                series.append((date, latest_market_value - latest_cost_value))
        return series

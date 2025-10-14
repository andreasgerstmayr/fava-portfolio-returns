import datetime
import itertools
from collections import defaultdict
from decimal import Decimal
from typing import NamedTuple

from beancount.core.inventory import Inventory
from beancount.core.number import ZERO

from fava_portfolio_returns._vendor.beangrow.investments import Cat
from fava_portfolio_returns._vendor.beangrow.investments import produce_cash_flows_general
from fava_portfolio_returns.core.portfolio import FilteredPortfolio
from fava_portfolio_returns.core.utils import cost_value_of_inv
from fava_portfolio_returns.core.utils import get_prices
from fava_portfolio_returns.core.utils import inv_to_currency
from fava_portfolio_returns.core.utils import market_value_of_inv


def portfolio_allocation(p: FilteredPortfolio, end_date: datetime.date):
    market_value_by_currency: dict[str, Decimal] = defaultdict(Decimal)
    for account_data in p.account_data_list:
        fp = FilteredPortfolio(p.portfolio, [account_data], p.target_currency)
        balance = fp.balance_at(end_date)
        market_value = market_value_of_inv(fp.pricer, fp.target_currency, balance, end_date)
        market_value_by_currency[account_data.currency] += market_value

    currency_name_by_currency = {cur.currency: cur.name for cur in p.portfolio.investments_config.currencies}
    return [
        {
            "name": currency_name_by_currency[currency],
            "currency": currency,
            "marketValue": market_value,
        }
        for currency, market_value in sorted(market_value_by_currency.items(), key=lambda x: x[1], reverse=True)
        if market_value > ZERO
    ]


class PortfolioValue(NamedTuple):
    date: datetime.date
    # market value
    market: Decimal
    # cost value (excl. fees)
    cost: Decimal
    # cumulative value of cash flows, i.e. cost value incl. fees
    cash: Decimal


def portfolio_values(
    p: FilteredPortfolio,
    start_date: datetime.date,
    end_date: datetime.date,
) -> list[PortfolioValue]:
    """returns (date,market,cost,cash) for all price and volume changes"""
    transactions = [txn for ad in p.account_data_list for txn in ad.transactions if txn.date <= end_date]

    # Infer the list of required prices.
    currency_pairs: set[tuple[str, str]] = set()
    for transaction in transactions:
        for posting in transaction.postings:
            if (
                posting.meta
                and posting.meta["category"] is Cat.ASSET
                and posting.cost
                and posting.units
                and posting.cost.currency
            ):
                # ex. (CORP, USD)
                currency_pairs.add((posting.units.currency, posting.cost.currency))

    def first(x):
        return x[0]

    # Get dates of transactions and price directives
    entry_dates = sorted(
        itertools.chain(
            (
                (date, None)
                for pair in currency_pairs
                for date, _ in get_prices(p.pricer, pair[0], pair[1])
                if date <= end_date
            ),
            ((entry.date, entry) for entry in transactions),  # already filtered above
        ),
        key=first,
    )

    # Skip price dates before first purchase of commodity (first transaction)
    for i, entry_date in enumerate(entry_dates):
        if entry_date[1] is not None:
            entry_dates = entry_dates[i:]
            break

    # Get first date of series, either before or on start_date.
    first_date = None
    for i, entry_date in enumerate(entry_dates):
        # if the next entry is still before or at start date, continue...
        if i + 1 < len(entry_dates) and entry_dates[i + 1][0] <= start_date:
            continue

        first_date = entry_date[0]
        break
    if not first_date:
        # This can only happen if entry_dates is empty.
        return []

    # Iterate computing the balance.
    values: list[PortfolioValue] = []
    balance = Inventory()
    cf_balance = Inventory()
    for date, group in itertools.groupby(entry_dates, key=first):
        # Update balances.
        for _, entry in group:
            if entry is None:
                continue
            for posting in entry.postings:
                if posting.meta and posting.meta["category"] is Cat.ASSET:
                    balance.add_position(posting)
            for flow in produce_cash_flows_general(entry, ""):
                cf_balance.add_amount(flow.amount)

        if date >= first_date:
            # Clamp start_date in case we cut off data at the beginning.
            clamp_date = max(date, start_date)
            market = market_value_of_inv(p.pricer, p.target_currency, balance, clamp_date)
            cost = cost_value_of_inv(p.pricer, p.target_currency, balance)
            cash = -inv_to_currency(p.pricer, p.target_currency, cf_balance)  # sum of cash flows
            values.append(PortfolioValue(date=clamp_date, market=market, cost=cost, cash=cash))

    return values

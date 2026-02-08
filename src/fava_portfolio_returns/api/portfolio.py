import datetime
import itertools
from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal

from beancount.core.inventory import Inventory
from beancount.core.number import ZERO

from fava_portfolio_returns._vendor.beangrow.investments import AccountData
from fava_portfolio_returns._vendor.beangrow.investments import Cat
from fava_portfolio_returns._vendor.beangrow.investments import Currency
from fava_portfolio_returns._vendor.beangrow.investments import produce_cash_flows_general
from fava_portfolio_returns.core.portfolio import FilteredPortfolio
from fava_portfolio_returns.core.utils import cost_value_of_inv
from fava_portfolio_returns.core.utils import get_prices
from fava_portfolio_returns.core.utils import market_value_of_inv


def portfolio_allocation(p: FilteredPortfolio, end_date: datetime.date):
    currency_by_code = {c.currency: c for c in p.portfolio.investments_config.currencies}
    account_data_by_currency: dict[Currency, list[AccountData]] = defaultdict(list)
    for account_data in p.account_data_list:
        account_data_by_currency[account_data.currency].append(account_data)

    allocations = []
    for currency_code, account_data_list in account_data_by_currency.items():
        fp = FilteredPortfolio(p.portfolio, account_data_list, p.target_currency)
        balance = fp.balance_at(end_date)
        market_value = market_value_of_inv(fp.pricer, fp.target_currency, balance, end_date)
        if market_value == ZERO:
            continue

        currency = currency_by_code[currency_code]
        allocations.append(
            {
                "id": currency.id,
                "name": currency.name,
                "currency": currency.currency,
                "marketValue": market_value,
            }
        )

    return sorted(allocations, key=lambda x: x["marketValue"], reverse=True)


@dataclass(frozen=True, slots=True)
class PortfolioValue:
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
                # also add data points for indirect conversion to target currency
                if posting.cost.currency != p.target_currency:
                    currency_pairs.add((posting.cost.currency, p.target_currency))

    def first(x):
        return x[0]

    # Get dates of transactions and price directives
    entry_dates = sorted(
        itertools.chain(
            (
                (date, None)
                for source, target in currency_pairs
                for date, _ in get_prices(p.pricer, source, target)
                if date <= end_date
            ),
            ((txn.date, txn) for txn in transactions),  # already filtered above
        ),
        key=first,
    )

    # Skip price dates before first purchase of commodity (first transaction)
    for i, entry_date in enumerate(entry_dates):
        if entry_date[1] is not None:
            entry_dates = entry_dates[i:]
            break

    # Get first date of series, either before or on start_date.
    # Example: start_date=7; entry_dates=[2, 5, 9, 10]; first_date=5 (will be clamped to 7)
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
    cf_balance_converted = Decimal(0.0)
    for date, group in itertools.groupby(entry_dates, key=first):
        # Update balances.
        for _, entry in group:
            if entry is None:
                continue
            for posting in entry.postings:
                if posting.meta and posting.meta["category"] is Cat.ASSET:
                    balance.add_position(posting)
            for flow in produce_cash_flows_general(entry, ""):
                # Convert flow amount to the target_currency at the date of the flow
                cash_amount_converted = p.pricer.convert_amount(flow.amount, p.target_currency, date)
                cf_balance_converted += cash_amount_converted.number

        if date >= first_date:
            # Clamp start_date in case we cut off data at the beginning.
            clamp_date = max(date, start_date)
            market = market_value_of_inv(p.pricer, p.target_currency, balance, clamp_date)
            cost = cost_value_of_inv(p.pricer, p.target_currency, balance, clamp_date)
            cash = -cf_balance_converted  # sum of cash flows
            values.append(PortfolioValue(date=clamp_date, market=market, cost=cost, cash=cash))

    return values

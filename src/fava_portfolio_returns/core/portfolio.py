import datetime
import itertools
from decimal import Decimal
from pathlib import Path
from typing import Any
from typing import NamedTuple
from typing import Optional

from beancount.core import getters
from beancount.core import prices
from beancount.core.data import Commodity
from beancount.core.data import Directive
from beancount.core.inventory import Inventory
from fava.beans.types import BeancountOptions
from fava.helpers import FavaAPIError

from fava_portfolio_returns._vendor.beangrow.config import read_config
from fava_portfolio_returns._vendor.beangrow.config import read_config_from_string
from fava_portfolio_returns._vendor.beangrow.investments import Account
from fava_portfolio_returns._vendor.beangrow.investments import AccountData
from fava_portfolio_returns._vendor.beangrow.investments import CashFlow
from fava_portfolio_returns._vendor.beangrow.investments import Cat
from fava_portfolio_returns._vendor.beangrow.investments import extract
from fava_portfolio_returns._vendor.beangrow.returns import Pricer
from fava_portfolio_returns.core.utils import inv_to_currency


class InvestmentAccount(NamedTuple):
    id: str
    currency: str
    assetAccount: str


class InvestmentGroup(NamedTuple):
    id: str
    name: str
    investments: list[str]
    currency: str


class LedgerCurrency(NamedTuple):
    id: str
    currency: str
    name: str
    isInvestment: bool


class InvestmentsConfig(NamedTuple):
    accounts: list[InvestmentAccount]
    groups: list[InvestmentGroup]
    currencies: list[LedgerCurrency]


class Portfolio:
    """Like a ledger, but for a portfolio of investments."""

    pricer: Pricer
    beangrow_cfg: Any
    account_data_map: dict[Account, AccountData]  # list of investments defined in beangrow config
    investments_config: InvestmentsConfig

    def __init__(
        self,
        entries: list[Directive],
        options_map: BeancountOptions,
        beangrow_config: Path | str,
        beangrow_debug_dir: Optional[str] = None,
    ):
        dcontext = options_map["dcontext"]
        accounts = getters.get_accounts(entries)
        price_map = prices.build_price_map(entries)
        self.pricer = Pricer(price_map)

        if isinstance(beangrow_config, Path):
            try:
                self.beangrow_cfg = read_config(beangrow_config.as_posix(), [], list(accounts))
            except Exception as ex:
                raise FavaAPIError(
                    f"Cannot read beangrow configuration file {beangrow_config.as_posix()}: {ex}"
                ) from ex
        else:
            self.beangrow_cfg = read_config_from_string(beangrow_config, [], list(accounts))

        self.account_data_map = extract(
            entries, dcontext, self.beangrow_cfg, entries[-1].date, False, beangrow_debug_dir or ""
        )
        inv_accounts = [
            InvestmentAccount(
                id=f"a:{investment.asset_account}",
                currency=investment.currency,
                assetAccount=investment.asset_account,
            )
            for investment in self.beangrow_cfg.investments.investment
        ]
        groups = [
            InvestmentGroup(
                id=f"g:{group.name}", name=group.name, investments=list(group.investment), currency=group.currency
            )
            for group in self.beangrow_cfg.groups.group
        ]
        currencies = get_ledger_currencies(entries, self.account_data_map)
        self.investments_config = InvestmentsConfig(accounts=inv_accounts, groups=groups, currencies=currencies)

    def filter(self, investment_filter: list[str], target_currency: Optional[str]):
        account_data_list = filter_investments(self.investments_config, self.account_data_map, investment_filter)
        if not target_currency:
            target_currency = get_target_currency(account_data_list)
        return FilteredPortfolio(self, account_data_list, target_currency)

    def get_missing_prices(self) -> tuple[list[dict], list[str]]:
        commodity_sources: dict[str, Optional[str]] = {}
        for account in self.account_data_map.values():
            commodity = account.commodity
            if commodity.currency not in commodity_sources:
                commodity_sources[commodity.currency] = commodity.meta.get("price")

        # sort by date and currency
        required_prices = sorted(self.pricer.required_prices.items(), key=lambda x: (x[0][1], x[0][0]))

        today = datetime.date.today()
        missing_prices: list[dict] = []
        commands: list[str] = []
        for date, group in itertools.groupby(required_prices, key=lambda x: x[0][1]):
            sources = []
            for (currency, required_date), found_dates in group:
                if len(found_dates) != 1:
                    raise ValueError(f"Found multiple prices for {currency} on {required_date}: {found_dates}")

                _cost_currency, actual_date, _rate = list(found_dates)[0]
                days_late = (required_date - actual_date).days
                if days_late < 5 or required_date > today:
                    continue

                missing_prices.append(
                    {
                        "currency": currency,
                        "requiredDate": required_date,
                        "actualDate": actual_date,
                        "daysLate": days_late,
                    }
                )
                source = commodity_sources.get(currency)
                if source:
                    sources.append(f"'{source}'")
            if sources:
                commands.append(f"bean-price -d '{date}' -e {' '.join(sources)}")
        return missing_prices, commands


class FilteredPortfolio:
    """A portfolio, filtered by investments.

    No filtering based on date range is done. Every method must handle start_date/end_date individually,
    because the handling is different, for example:
    * list of cash flows: can be cut off based on dates
    * portfolio cost value: cost value must be a cumulative sum
    """

    portfolio: Portfolio
    account_data_list: list[AccountData]
    target_currency: str

    def __init__(self, portfolio: Portfolio, account_data_list: list[AccountData], target_currency: str):
        self.portfolio = portfolio
        self.account_data_list = account_data_list
        self.target_currency = target_currency

    @property
    def pricer(self):
        return self.portfolio.pricer

    def cash_flows(self) -> list[CashFlow]:
        """returns a list of all cash flows"""
        cash_flows: list[CashFlow] = []
        for account_data in self.account_data_list:
            cash_flows.extend(account_data.cash_flows)
        cash_flows.sort(key=lambda flow: flow.date)
        return cash_flows

    def balance_at(self, date: datetime.date):
        """returns the inventory at the given date"""
        balance = Inventory()
        for account_data in self.account_data_list:
            for entry in account_data.transactions:
                if entry.date > date:
                    break
                for posting in entry.postings:
                    if posting.meta and posting.meta["category"] is Cat.ASSET:
                        balance.add_position(posting)
        return balance

    def cash_at(self, date: datetime.date) -> Decimal:
        """returns the sum of all cash flows until the given date"""
        balance = Inventory()
        for account_data in self.account_data_list:
            for cash_flow in account_data.cash_flows:
                if cash_flow.date > date:
                    break
                balance.add_amount(cash_flow.amount)
        return -inv_to_currency(self.pricer, self.target_currency, balance)


def get_target_currency(account_data_list: list[AccountData]) -> str:
    cost_currencies = set(ad.cost_currency for ad in account_data_list)
    if len(cost_currencies) != 1:
        curr = ", ".join(cost_currencies)
        accs = ", ".join([ad.account for ad in account_data_list])
        raise FavaAPIError(
            f"Found multiple cost currencies {curr} for accounts {accs}."
            " Please specify a single currency for the group in the beangrow configuration file."
        )
    return cost_currencies.pop()


def filter_investments(
    investment_groups: InvestmentsConfig,
    account_data_map: dict[str, AccountData],
    investment_filter: list[str],
) -> list[AccountData]:
    accounts = set()

    if investment_filter:
        for account in investment_groups.accounts:
            if account.id in investment_filter:
                accounts.add(account.assetAccount)

        for group in investment_groups.groups:
            if group.id in investment_filter:
                accounts.update(group.investments)

        for currency in investment_groups.currencies:
            if currency.id in investment_filter:
                for account_data in account_data_map.values():
                    if account_data.currency == currency.currency:
                        accounts.add(account_data.account)
    else:
        accounts.update(account_data_map.keys())

    return [account_data_map[account] for account in accounts]


def get_ledger_currencies(entries: list[Directive], account_data_map: dict[str, AccountData]) -> list[LedgerCurrency]:
    investment_currencies = set()
    for account in account_data_map.values():
        investment_currencies.add(account.currency)
    currencies = [
        LedgerCurrency(
            id=f"c:{c.currency}",
            name=c.meta.get("name", c.currency),
            currency=c.currency,
            isInvestment=c.currency in investment_currencies,
        )
        for c in entries
        if isinstance(c, Commodity)
    ]
    return currencies

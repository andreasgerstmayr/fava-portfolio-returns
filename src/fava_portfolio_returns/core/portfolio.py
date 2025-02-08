import datetime
import itertools
from decimal import Decimal
from pathlib import Path
from typing import Any
from typing import NamedTuple
from typing import Optional

import beangrow.config as configlib
import beangrow.investments
from beancount.core import getters
from beancount.core import prices
from beancount.core.data import Directive
from beancount.core.inventory import Inventory
from beangrow import config_pb2
from beangrow.investments import Account
from beangrow.investments import AccountData
from beangrow.investments import CashFlow
from beangrow.investments import Cat
from beangrow.returns import Pricer
from fava.beans.types import BeancountOptions
from fava.helpers import FavaAPIError
from google.protobuf import text_format

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


class InvestmentCurrency(NamedTuple):
    id: str
    currency: str
    name: str


class InvestmentGroups(NamedTuple):
    accounts: list[InvestmentAccount]
    groups: list[InvestmentGroup]
    currencies: list[InvestmentCurrency]


class Portfolio:
    """Like a ledger, but for a portfolio of investments."""

    pricer: Pricer
    beangrow_cfg: Any
    account_data_map: dict[Account, AccountData]
    investment_groups: InvestmentGroups

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
            self.beangrow_cfg = read_beangrow_config_from_file(beangrow_config.as_posix(), accounts)
        else:
            self.beangrow_cfg = read_beangrow_config_from_string(beangrow_config, accounts)

        self.account_data_map = beangrow.investments.extract(
            entries, dcontext, self.beangrow_cfg, entries[-1].date, False, beangrow_debug_dir
        )
        self.account_data_list = list(self.account_data_map.values())
        self.investment_groups = group_investments(self.beangrow_cfg, self.account_data_map)

    def filter(self, investment_filter: list[str], target_currency: Optional[str]):
        account_data_list = filter_investments(self.investment_groups, self.account_data_map, investment_filter)
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
                    if posting.meta["category"] is Cat.ASSET:
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


def read_beangrow_config_from_file(config_filename: str, accounts: set[str]):
    try:
        config = configlib.read_config(config_filename, [], accounts)
    except Exception as ex:
        raise FavaAPIError(f"Cannot read beangrow configuration file {config_filename}: {ex}") from ex
    return config


# like beangrow.config.read_config, but with the config file as string
# TODO: use read_config_from_string() from beangrow once beangrow 1.0.2 is released
def read_beangrow_config_from_string(config_text: str, accounts: set[str]):
    # Read the file.
    config = config_pb2.Config()
    text_format.Merge(config_text, config)

    # Expand account names.
    for investment in config.investments.investment:
        assert not configlib.is_glob(investment.asset_account)
        investment.dividend_accounts[:] = configlib.expand_globs(investment.dividend_accounts, accounts)
        investment.match_accounts[:] = configlib.expand_globs(investment.match_accounts, accounts)
        investment.cash_accounts[:] = configlib.expand_globs(investment.cash_accounts, accounts)

    # Expand investment names.
    investment_names = [investment.asset_account for investment in config.investments.investment]
    for report in config.groups.group:
        report.investment[:] = configlib.expand_globs(report.investment, investment_names)

    # Filter just the list of investments needed for the reports defined.
    used_investments = set(inv for report in config.groups.group for inv in report.investment)
    investments = [invest for invest in config.investments.investment if invest.asset_account in used_investments]
    del config.investments.investment[:]
    config.investments.investment.extend(investments)

    return config


def group_investments(config, account_data_map: dict[str, AccountData]):
    accounts: list[InvestmentAccount] = []
    for investment in config.investments.investment:
        accounts.append(
            InvestmentAccount(
                id=f"a:{investment.asset_account}",
                currency=investment.currency,
                assetAccount=investment.asset_account,
            )
        )

    groups: list[InvestmentGroup] = []
    for group in config.groups.group:
        groups.append(
            InvestmentGroup(
                id=f"g:{group.name}", name=group.name, investments=list(group.investment), currency=group.currency
            )
        )

    currencies: dict[str, InvestmentCurrency] = {}
    for account in account_data_map.values():
        if account.currency not in currencies:
            currencies[account.currency] = InvestmentCurrency(
                id=f"c:{account.currency}",
                name=account.commodity.meta.get("name", account.currency),
                currency=account.currency,
            )
    currencies_list = sorted(currencies.values(), key=lambda x: x.id)

    return InvestmentGroups(accounts=accounts, groups=groups, currencies=currencies_list)


def filter_investments(
    investment_groups: InvestmentGroups,
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

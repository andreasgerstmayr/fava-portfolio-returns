from pathlib import Path
from typing import Any, NamedTuple, Optional

import beangrow.config as configlib
import beangrow.investments
from beancount.core import getters, prices
from beancount.core.data import Directive
from beangrow import config_pb2
from beangrow.investments import Account, AccountData
from beangrow.returns import Pricer
from fava.beans.types import BeancountOptions
from fava.helpers import FavaAPIError
from google.protobuf import text_format


class InvestmentAccount(NamedTuple):
    id: str
    currency: str
    assetAccount: str


class InvestmentGroup(NamedTuple):
    id: str
    name: str
    investments: list[str]


class InvestmentCurrency(NamedTuple):
    id: str
    currency: str
    name: str


class InvestmentGroups(NamedTuple):
    accounts: list[InvestmentAccount]
    groups: list[InvestmentGroup]
    currencies: list[InvestmentCurrency]


class Portfolio:
    """
    Like a ledger, but for a portfolio of investments.

    It can be filtered by investments (investment_filter), but no filtering based on date range is done.
    Every method must handle start_date/end_date individually, because the handling is different:
    * list of cash flows: can be cut off
    * portfolio cost value: cash flows must be truncated (cumulate value before the cut off date)
    """

    pricer: Pricer
    beangrow_cfg: Any
    account_data_map: dict[Account, AccountData]
    account_data_list: list[AccountData]
    investment_groups: InvestmentGroups

    def __init__(
        self,
        entries: list[Directive],
        options: BeancountOptions,
        beangrow_config: Path | str,
        beangrow_debug_dir: Optional[str] = None,
    ):
        dcontext = options["dcontext"]
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

    def filter_account_data_list(self, investment_filter: Optional[list[str]] = []):
        return filter_investments(self.investment_groups, self.account_data_map, investment_filter)


def read_beangrow_config_from_file(config_filename: str, accounts: set[str]):
    try:
        config = configlib.read_config(config_filename, None, accounts)
    except Exception as ex:
        raise FavaAPIError(f"Cannot read beangrow configuration file {config_filename}: {ex}") from ex
    return config


# like beangrow.config.read_config, but with the config file as string
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
        groups.append(InvestmentGroup(id=f"g:{group.name}", name=group.name, investments=list(group.investment)))

    currencies: dict[str, InvestmentCurrency] = {}
    for account in account_data_map.values():
        if account.currency not in currencies:
            currencies[account.currency] = InvestmentCurrency(
                id=f"c:{account.currency}", currency=account.currency, name=account.commodity.meta["name"]
            )
    currencies_list = sorted(currencies.values(), key=lambda x: x.id)

    return InvestmentGroups(accounts=accounts, groups=groups, currencies=currencies_list)


def filter_investments(
    investments: InvestmentGroups, account_data_map: dict[str, AccountData], investment_filter: Optional[list[str]] = []
) -> list[AccountData]:
    accounts = set()

    if investment_filter:
        for account in investments.accounts:
            if account.id in investment_filter:
                accounts.add(account.assetAccount)

        for group in investments.groups:
            if group.id in investment_filter:
                accounts.update(group.investments)

        for currency in investments.currencies:
            if currency.id in investment_filter:
                for account_data in account_data_map.values():
                    if account_data.currency == currency.currency:
                        accounts.add(account_data.account)
    else:
        accounts.update(account_data_map.keys())

    return [account_data_map[account] for account in accounts]

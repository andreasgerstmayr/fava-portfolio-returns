import datetime
from collections import defaultdict
from decimal import Decimal
from pathlib import Path
from typing import Any
from typing import Collection
from typing import Optional
from typing import Sequence

from beancount.core.data import Directive
from beancount.core.data import Transaction
from beancount.core.inventory import Inventory
from beancount.core.number import ZERO
from fava.helpers import FavaAPIError

from fava_portfolio_returns.api.asset_allocation_core import AssetAllocationError
from fava_portfolio_returns.api.asset_allocation_core import Band
from fava_portfolio_returns.api.asset_allocation_core import LoadedConfig
from fava_portfolio_returns.api.asset_allocation_core import PortfolioConfig
from fava_portfolio_returns.api.asset_allocation_core import bucket_commodities
from fava_portfolio_returns.api.asset_allocation_core import compile_account_patterns
from fava_portfolio_returns.api.asset_allocation_core import load_config
from fava_portfolio_returns.api.asset_allocation_core import minimal_split
from fava_portfolio_returns.api.asset_allocation_core import proportional_split
from fava_portfolio_returns.api.asset_allocation_core import resolve_band
from fava_portfolio_returns.api.asset_allocation_core import resolve_item_thresholds
from fava_portfolio_returns.api.asset_allocation_core import target_sum
from fava_portfolio_returns.core.pricer import CurrencyConversionException
from fava_portfolio_returns.core.pricer import Pricer
from fava_portfolio_returns.core.utils import market_value_of_inv


def load_asset_allocation_config(path: Path) -> LoadedConfig:
    """Load the target asset allocation from a YAML configuration file.

    The format is documented in, and parsed by, `asset_allocation_core`; the
    same file can be shared with other tools reading it. A target block that
    does not sum to 100% is reported to the frontend rather than refused (see
    `target_sum`), so the report still renders with the problem visible.
    """
    try:
        return load_config(path)
    except AssetAllocationError as ex:
        # the API surfaces one message; the rest would not fit the error banner
        raise FavaAPIError(f"{path}: {ex.errors[0]}") from ex


def portfolio_holdings(
    entries: Sequence[Directive],
    pricer: Pricer,
    accounts: list[str],
    target_currency: str,
    end_date: datetime.date,
    cash_currencies: Optional[Collection[str]] = None,
) -> tuple[dict[str, Decimal], list[str]]:
    """Return the current market value per commodity of a portfolio.

    `accounts` is a list of account regexes (OR-combined, matched unanchored
    like Beanquery's `~` operator). Holdings are valued in `target_currency` at
    the latest known prices as of `end_date`. The portfolio's cash holdings
    (positions in `cash_currencies`, by default just `target_currency`) are
    ignored. Pass the ledger's operating currencies, so that what counts as
    cash does not change with the currency the report is valued in.

    Returns a pair ``(values, unpriced)`` where `values` maps commodity ->
    current market value, and `unpriced` lists held commodities that could not
    be valued (no known price).
    """
    try:
        patterns = compile_account_patterns(accounts)
    except AssetAllocationError as ex:
        raise FavaAPIError(ex.errors[0]) from ex

    cash = {target_currency} if cash_currencies is None else set(cash_currencies)
    balances: dict[str, Inventory] = defaultdict(Inventory)
    for entry in entries:
        if not isinstance(entry, Transaction) or entry.date > end_date:
            continue
        for posting in entry.postings:
            if posting.units is None or posting.units.currency in cash:
                continue
            if any(pattern.search(posting.account) for pattern in patterns):
                balances[posting.units.currency].add_position(posting)

    values: dict[str, Decimal] = {}
    unpriced: list[str] = []
    for commodity, balance in balances.items():
        if balance.is_empty():
            continue  # no current holdings (e.g. fully liquidated)
        try:
            market_value = market_value_of_inv(
                pricer, target_currency, balance, end_date
            )
        except CurrencyConversionException:
            unpriced.append(commodity)
            continue
        if market_value != ZERO:
            values[commodity] = market_value
    return values, sorted(unpriced)


def _deviation(
    cur_value: Decimal, target_pct: Decimal, total_value: Decimal
) -> tuple[Decimal, Decimal, Decimal]:
    """Return ``(cur_pct, dev_pct, dev_value)`` for a holding vs. its target.

    A positive deviation means overweight (suggesting to sell), negative
    underweight (suggesting to buy).
    """
    cur_pct = (cur_value * 100 / total_value) if total_value else ZERO
    target_value = target_pct * total_value / 100
    return cur_pct, cur_pct - target_pct, cur_value - target_value


def report_portfolio_commodities(
    config: PortfolioConfig,
    values: dict[str, Decimal],
    thresholds: dict[str, Decimal],
    names: dict[str, str],
) -> dict:
    """Build the by-commodity sub-report for a single portfolio.

    Compares the current allocation (`values`) against the target allocation and
    computes, per configured commodity, the current and target weights and the
    deviation (in percentage points and in the target currency). `thresholds`
    gives the divergence threshold of each configured commodity, derived from
    its own target (see `resolve_item_thresholds`) and hence generally its own.
    """
    total_value = sum(values.values(), ZERO)

    assets = []
    diverged = False
    for commodity, target_pct in config.commodity_targets.items():
        cur_value = values.get(commodity, ZERO)
        cur_pct, dev_pct, dev_value = _deviation(cur_value, target_pct, total_value)
        # Strict '>' is intentional: an asset exactly at the threshold is not flagged.
        over = abs(dev_pct) > thresholds[commodity]
        diverged = diverged or over

        assets.append(
            {
                "commodity": commodity,
                "name": names.get(commodity, commodity),
                "targetPct": target_pct,
                "currentPct": cur_pct,
                "value": cur_value,
                "devPct": dev_pct,
                "devValue": dev_value,
                "over": over,
                "thresholdPct": thresholds[commodity],
            }
        )

    # held commodities that are not part of the target allocation
    unconfigured = [
        {
            "commodity": commodity,
            "name": names.get(commodity, commodity),
            "value": values[commodity],
        }
        for commodity in sorted(set(values) - set(config.commodity_targets))
    ]

    total_target, target_sum_ok = target_sum(config.commodity_targets)
    return {
        "diverged": diverged,
        "assets": assets,
        "unconfigured": unconfigured,
        "targetSum": total_target,
        "targetSumOk": target_sum_ok,
    }


def report_portfolio_classes(
    config: PortfolioConfig,
    values: dict[str, Decimal],
    asset_classes: dict[str, str],
    thresholds: dict[str, Decimal],
    commodity_thresholds: dict[str, Decimal],
    names: dict[str, str],
    minimize: bool,
) -> dict:
    """Build the by-asset-class sub-report for a single portfolio.

    Each held commodity is bucketed into its most-specific configured class.
    Under each class, concrete per-commodity buy/sell suggestions are computed;
    in aggregate they close the class's gap (proportional to current value by
    default; by fewest commodities with `minimize`, which is where
    `commodity_thresholds` bound the individual trades). `thresholds` gives the
    divergence threshold of each configured class.
    """
    targets = list(config.class_targets)
    total_value = sum(values.values(), ZERO)
    members, unconfigured = bucket_commodities(values, asset_classes, targets)

    classes = []
    diverged = False
    for asset_class in targets:
        target_pct = config.class_targets[asset_class]
        holdings = members[asset_class]
        cur_value = sum(holdings.values(), ZERO)
        cur_pct, dev_pct, dev_value = _deviation(cur_value, target_pct, total_value)
        over = abs(dev_pct) > thresholds[asset_class]
        diverged = diverged or over

        # per-commodity rebalance breakdown for this class
        member_trades = []
        shortfall = ZERO
        if ZERO not in (dev_value, cur_value):
            if minimize:
                shares, shortfall = minimal_split(
                    dev_value,
                    holdings,
                    config.commodity_targets,
                    total_value,
                    commodity_thresholds,
                )
            else:
                shares = proportional_split(dev_value, holdings, cur_value)
            member_trades = [
                {
                    "commodity": commodity,
                    "name": names.get(commodity, commodity),
                    "value": value,
                    "tradeValue": amount,  # positive => sell, negative => buy
                }
                for commodity, value, amount in shares
            ]

        classes.append(
            {
                "assetClass": asset_class,
                "targetPct": target_pct,
                "currentPct": cur_pct,
                "value": cur_value,
                "devPct": dev_pct,
                "devValue": dev_value,
                "over": over,
                "members": member_trades,
                "noHoldings": cur_value == ZERO,
                "shortfall": shortfall,
                "thresholdPct": thresholds[asset_class],
            }
        )

    total_target, target_sum_ok = target_sum(config.class_targets)
    return {
        "diverged": diverged,
        "minimize": minimize,
        "classes": classes,
        "unconfigured": [
            {
                "commodity": commodity,
                "name": names.get(commodity, commodity),
                "value": value,
                "reason": reason,
            }
            for commodity, value, reason in sorted(unconfigured)
        ],
        "targetSum": total_target,
        "targetSumOk": target_sum_ok,
    }


def asset_allocation_report(
    entries: Sequence[Directive],
    pricer: Pricer,
    portfolios: list[PortfolioConfig],
    target_currency: str,
    end_date: datetime.date,
    default_band: Band = Band(),
    asset_classes: Optional[dict[str, str]] = None,
    names: Optional[dict[str, str]] = None,
    minimize: bool = False,
    cash_currencies: Optional[Collection[str]] = None,
) -> list[dict]:
    """Build the asset allocation report for all configured portfolios.

    Each portfolio emits a `commodityReport` and/or a `classReport` sub-report,
    depending on which target blocks it defines. `default_band` is the
    file-level divergence band, applying to the portfolios that do not tighten
    it; each individual target may tighten the portfolio's in turn, and every
    band is worked out against its own target (see `resolve_band` and
    `resolve_item_thresholds`). `cash_currencies` is passed on to
    `portfolio_holdings`.
    """
    asset_classes = asset_classes or {}
    names = names or {}
    reports = []
    for config in portfolios:
        values, unpriced = portfolio_holdings(
            entries, pricer, config.accounts, target_currency, end_date, cash_currencies
        )
        band = resolve_band(config, default_band)
        commodity_thresholds = resolve_item_thresholds(config, "commodity", band)
        class_thresholds = resolve_item_thresholds(config, "class", band)
        report: dict[str, Any] = {
            "name": config.name,
            "accounts": config.accounts,
            "currency": target_currency,
            "totalValue": sum(values.values(), ZERO),
            # the rule, not a number: each row's own band is in its thresholdPct
            "band": {"ofPortfolio": band.of_portfolio, "ofTarget": band.of_target},
            "unpriced": unpriced,
            "commodityReport": None,
            "classReport": None,
        }
        if config.commodity_targets:
            report["commodityReport"] = report_portfolio_commodities(
                config, values, commodity_thresholds, names
            )
        if config.class_targets:
            report["classReport"] = report_portfolio_classes(
                config,
                values,
                asset_classes,
                class_thresholds,
                commodity_thresholds,
                names,
                minimize,
            )
        reports.append(report)
    return reports

"""Target asset allocation: configuration format and rebalancing arithmetic.

Deliberately self-contained (stdlib, beancount, PyYAML), to ease sharing among multiple
asset allocation tools.

The configuration file format::

    asset-class-key: asset-class  # optional; commodity metadata key holding the
                                  # (hierarchical, ':'-separated) asset class
    divergence-threshold:         # optional; the default divergence band. Can
      of-portfolio: 5%            # be overridden per portfolio and per target
      of-target: 25%              # (both below)
    portfolios:
      - name: My Portfolio
        accounts:                 # one or more account regexes
          - "^Assets:Broker:Investments:"
        divergence-threshold:     # optional; overrides the top-level one, for
          of-portfolio: 3%        # this portfolio only
        allocation:               # the target asset allocation, by...
          commodities:            # ... per-commodity target, summing to 100%
            - commodity: ETF_FOO
              target: 60%
              divergence-threshold:   # optional; overrides the portfolio's,
                of-target: 10%        # for this commodity only
            - commodity: ETF_BAR
              target: 40%
          classes:                # ... per-asset-class target, summing to 100%
            - asset-class: stocks
              target: 70%
            - asset-class: bonds
              target: 30%

A divergence band caps how far a target may drift before it is flagged, from two sides:
`of-portfolio` in percentage points of the portfolio, `of-target` as a fraction of the
target itself. They combine with min(), so the band of a small sleeve is tight without
the large ones being held to the same absolute figure.

The two sides are resolved SEPARATELY and most-specific-first: the individual target's
own `divergence-threshold`, the portfolio's, the top-level one, and finally
DEFAULT_BAND.  A block that sets only one side keeps inheriting the other. Every band is
worked out against its own target, so the configuration states a rule, not a number.

"""

import re
from dataclasses import dataclass
from dataclasses import field
from decimal import ROUND_HALF_EVEN
from decimal import Decimal
from typing import Any
from typing import Iterable
from typing import NamedTuple
from typing import Optional

import yaml
from beancount.core.data import Commodity

__version__ = "1.0.0"

# how close to 100% a target allocation must sum (rounding tolerance)
SUM_TOLERANCE = Decimal("0.1")

# default commodity metadata key holding the (hierarchical) asset class
DEFAULT_ASSET_CLASS_KEY = "asset-class"

# target block name under a portfolio's 'allocation', per report kind
ALLOC_BLOCKS = {"commodity": "commodities", "class": "classes"}

# the per-entry key naming the item, per report kind
ITEM_KEYS = {"commodity": "commodity", "class": "asset-class"}

# the two sides of a divergence band, as named in the configuration file
BAND_KEYS = ("of-portfolio", "of-target")

# name given to a portfolio that does not state one, in reports and messages
UNNAMED = "<unnamed>"

# type aliases for the shapes that recur across the module
AmountMap = dict[str, Decimal]  # commodity/class -> amount or percentage
Members = dict[str, AmountMap]  # class -> its {commodity: value} holdings
Assignment = tuple[str, Decimal, Decimal]  # (commodity, value, trade amount)


class AssetAllocationError(ValueError):
    """One or more problems with an asset allocation configuration.

    Carries every message found rather than just the first, because a
    configuration is usually fixed in one pass and a tool reporting one typo at
    a time makes that needlessly slow. Consumers that can only show one thing
    take `errors[0]`; those that can, print them all.
    """

    def __init__(self, errors: "str | list[str]") -> None:
        self.errors = [errors] if isinstance(errors, str) else list(errors)
        super().__init__("; ".join(self.errors))


class Band(NamedTuple):
    """A divergence band, as two caps on how far a target may drift.

    `of_portfolio` is an absolute cap in percentage points of the portfolio; `of_target`
    a relative one, as a fraction of the target itself. They COMBINE WITH min():
    whichever is the smaller at a given target is the one that binds, so each is an
    independent upper bound on the band. An unset (None) side imposes no cap of its own.

    """

    of_portfolio: Optional[Decimal] = None  # percentage points of the portfolio
    of_target: Optional[Decimal] = None  # per cent of the target

    def merge(self, outer: "Band") -> "Band":
        """Return this band's set sides laid over `outer`'s, side by side.

        Merging rather than replacing is what lets one target tighten only its relative
        side while still inheriting the absolute cap from above.

        """
        return Band(
            self.of_portfolio if self.of_portfolio is not None else outer.of_portfolio,
            self.of_target if self.of_target is not None else outer.of_target,
        )

    def _check_set(self) -> None:
        """Guard the invariant that at least one side of the band is set.

        Callers reach a band through `resolve_band`, which merges it against
        DEFAULT_BAND, and the parser rejects a configured band with neither side set; so
        an all-unset one here is a programming error, not a user's. Refusing it beats
        treating it as "no cap at all", which is the one answer that would let a target
        drift unwatched in silence.

        """
        if self.of_portfolio is None and self.of_target is None:
            raise AssetAllocationError("divergence band has neither side set.")

    def width(self, target_pct: Decimal) -> Decimal:
        """The band this works out to, in percentage points, at `target_pct`."""
        self._check_set()
        caps = []
        if self.of_portfolio is not None:
            caps.append(self.of_portfolio)
        if self.of_target is not None:
            caps.append(self.of_target * target_pct / 100)
        return min(caps)

    def describe(self) -> str:
        """Spell the band out as the rule it is, for a report header."""
        self._check_set()
        caps = [
            f"{cap}% of {denominator}"
            for cap, denominator in (
                (self.of_portfolio, "portfolio"),
                (self.of_target, "target"),
            )
            if cap is not None
        ]
        return f"min({', '.join(caps)})" if len(caps) > 1 else caps[0]


# Larry Swedroe's 5/25 rule: rebalance when a holding drifts by more than an absolute 5
# percentage points or 25% of its own target, "whichever is less" -- Think, Act, and
# Invest Like Warren Buffett, ISBN 978-0-07-180995-5, quoted at
# https://awealthofcommonsense.com/2014/03/larry-swedroe-525-rebalancing-rule/
DEFAULT_BAND = Band(of_portfolio=Decimal(5), of_target=Decimal(25))


@dataclass(frozen=True)
class PortfolioConfig:
    """One portfolio's target asset allocation, parsed and validated.

    A portfolio may define per-commodity targets, per-asset-class targets, or both; each
    block (when present) should sum to 100%, which `target_sum` reports on and each
    consumer acts on in its own way.

    """

    name: str
    # account regexes (OR-combined), matched unanchored like Beanquery's `~`
    accounts: list[str]
    # commodity -> target allocation in percent (insertion-ordered)
    commodity_targets: AmountMap = field(default_factory=dict)
    # asset class -> target allocation in percent (insertion-ordered)
    class_targets: AmountMap = field(default_factory=dict)
    # the portfolio's own band, laid over the file-level one; sides it leaves unset are
    # inherited, so an all-unset band changes nothing
    divergence_band: Band = Band()
    # own bands of individual commodity targets, laid over the portfolio's the same way;
    # commodities absent from it inherit it whole
    commodity_bands: dict[str, Band] = field(default_factory=dict)
    # likewise for individual asset-class targets
    class_bands: dict[str, Band] = field(default_factory=dict)

    def targets(self, kind: str) -> AmountMap:
        """The target percentages of report `kind` ('commodity' or 'class')."""
        return self.commodity_targets if kind == "commodity" else self.class_targets

    def bands(self, kind: str) -> dict[str, Band]:
        """The per-target band overrides of report `kind`."""
        return self.commodity_bands if kind == "commodity" else self.class_bands


@dataclass(frozen=True)
class LoadedConfig:
    """A whole configuration file, parsed and validated."""

    portfolios: list[PortfolioConfig]
    # commodity metadata key holding the (hierarchical, ':'-separated) asset class
    asset_class_key: str
    # the file-level divergence band, all-unset when the file states none
    default_band: Band


def parse_pct(value: Any) -> Decimal:
    """Parse a target percentage, accepting both '25%' and bare numbers.

    Raise ValueError on a non-finite value: YAML's '.nan' and '.inf' parse as numbers,
    and a NaN would raise InvalidOperation on the first range check.

    """
    if isinstance(value, str):
        value = value.strip().rstrip("%").strip()
    pct = Decimal(str(value))
    if not pct.is_finite():
        raise ValueError(f"non-finite percentage: {value}")
    return pct


def quantize(amount: Decimal) -> Decimal:
    """Round a currency amount to cents (banker's rounding)."""
    return amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN)


def target_sum(targets: AmountMap) -> tuple[Decimal, bool]:
    """Return ``(total, ok)`` for a target block, `ok` within SUM_TOLERANCE.

    Deliberately not part of validation: a block that does not sum to 100% is an error
    to a tool that must refuse to act on it, but merely something to flag to one that
    renders a report either way.

    """
    total = sum(targets.values(), Decimal(0))
    return total, abs(total - Decimal(100)) <= SUM_TOLERANCE


def _band_keys() -> str:
    return " and/or ".join(f"'{key}'" for key in BAND_KEYS)


def parse_band(value: Any) -> Band:
    """Parse and range-check a 'divergence-threshold' setting into a `Band`.

    The setting is a mapping of one or both of 'of-portfolio' and 'of-target'; a bare
    percentage is rejected, as it would silently mean "cap the absolute side and keep
    inheriting the relative one", which is not how a lone number reads. Raise
    `AssetAllocationError`, with a message the caller prefixes with the setting's
    location, on anything unparseable or out of range.

    """
    if not isinstance(value, dict):
        raise AssetAllocationError(
            f"divergence-threshold must be a mapping of {_band_keys()}, not '{value}'."
        )
    unknown = sorted(set(value) - set(BAND_KEYS))
    if unknown:
        raise AssetAllocationError(
            "unknown divergence-threshold key(s) "
            + ", ".join(f"'{key}'" for key in unknown)
            + f"; expected {_band_keys()}."
        )

    caps: dict[str, Optional[Decimal]] = {}
    for key in BAND_KEYS:
        if value.get(key) is None:
            caps[key] = None
            continue
        try:
            cap = parse_pct(value[key])
        except (ArithmeticError, ValueError) as ex:
            raise AssetAllocationError(
                f"invalid divergence-threshold {key} '{value[key]}'."
            ) from ex
        if not Decimal(0) <= cap <= Decimal(100):
            raise AssetAllocationError(
                f"divergence-threshold {key} {cap}% is out of range [0, 100]."
            )
        caps[key] = cap

    # An empty mapping, or one whose only side was written without a value
    # ("of-portfolio:" and nothing after it), states no cap at all. It would merge away
    # to pure inheritance -- the setting silently doing nothing, which is the failure
    # this whole shape exists to prevent.
    if all(cap is None for cap in caps.values()):
        raise AssetAllocationError(
            f"empty divergence-threshold; set {_band_keys()} to a percentage."
        )
    return Band(caps["of-portfolio"], caps["of-target"])


def own_band(block: dict) -> Band:
    """Return a config block's own divergence band, all-unset when it has none.

    Works for any block that may carry the setting: the file itself, a portfolio, or a
    single commodity/class entry of its target allocation. An all-unset band merges away
    to nothing, so callers need no special case for the common absence.

    Absent is fine; present but empty is not. 'divergence-threshold:' with nothing after
    it reads as an intent to set one, and inheriting silently would be the same failure
    `parse_band` rejects an empty mapping for.

    """
    if "divergence-threshold" not in block:
        return Band()
    value = block["divergence-threshold"]
    if value is None:
        raise AssetAllocationError(
            f"empty divergence-threshold; set {_band_keys()} to a percentage."
        )
    return parse_band(value)


def resolve_band(portfolio: PortfolioConfig, default_band: Band) -> Band:
    """Resolve the divergence band applying to one portfolio.

    Precedence, most specific first: the portfolio's own band, the file-level one, and
    finally DEFAULT_BAND — resolved SIDE BY SIDE, so a portfolio that sets only one of
    them keeps inheriting the other. Individual targets can tighten or loosen this in
    turn, see `resolve_item_thresholds`.

    """
    return portfolio.divergence_band.merge(default_band).merge(DEFAULT_BAND)


def resolve_item_thresholds(
    portfolio: PortfolioConfig, kind: str, fallback: Band
) -> AmountMap:
    """Map each target of report `kind` to the divergence threshold it uses.

    This is where a band becomes a number: each target's own band is laid over the
    portfolio-level `fallback` (itself already resolved by `resolve_band`) and then
    worked out against that target's own percentage, so a target and its band cannot
    fall out of step. Everything downstream sees plain percentage points.

    """
    bands = portfolio.bands(kind)
    return {
        item: bands.get(item, Band()).merge(fallback).width(target_pct)
        for item, target_pct in portfolio.targets(kind).items()
    }


def _alloc_entries(portfolio: dict, kind: str) -> Any:
    """Return a raw portfolio's target list for `kind`, as written in the file.

    Returns whatever the file holds, list or not; validation is what turns a wrong shape
    into a message. An absent 'allocation' yields an empty list.

    """
    allocation = portfolio.get("allocation")
    if not isinstance(allocation, dict):
        return []
    return allocation.get(ALLOC_BLOCKS[kind]) or []


def _validate_targets(
    name: str, entries: Any, kind: str, require_sum: bool
) -> tuple[AmountMap, dict[str, Band], list[str]]:
    """Validate one target block, returning ``(targets, bands, errors)``.

    `kind` selects the per-entry key naming the item ('commodity' or 'asset-class') and
    the word used in messages. Every problem is collected rather than raised, so one
    pass over a file reports all of them.

    `require_sum` turns a block that does not sum to 100% into one more error, for
    callers that must refuse to act on it; see `target_sum`.

    """
    item_key = ITEM_KEYS[kind]
    label = kind
    targets: AmountMap = {}
    bands: dict[str, Band] = {}
    errors: list[str] = []
    # summed over every entry parsed rather than over `targets`, so that a duplicated
    # item is counted as many times as it is written
    total = Decimal(0)

    for i, entry in enumerate(entries, start=1):
        if not isinstance(entry, dict):
            errors.append(f"portfolio '{name}': {label} #{i} is not a mapping.")
            continue
        if item_key not in entry:
            errors.append(f"portfolio '{name}': {label} #{i} is missing '{item_key}'.")
            continue
        item = entry[item_key]
        if not isinstance(item, str):
            errors.append(
                f"portfolio '{name}': {label} #{i} has a non-string "
                f"'{item_key}': '{item}'. Quote it."
            )
            continue

        if item in targets:
            errors.append(f"portfolio '{name}': duplicate {label} '{item}'.")

        try:
            band = own_band(entry)
        except AssetAllocationError as exc:
            errors.append(f"portfolio '{name}': {label} '{item}': {exc.errors[0]}")
            band = Band()
        if band != Band():
            bands[item] = band

        unknown = sorted(set(entry) - {item_key, "target", "divergence-threshold"})
        if unknown:
            errors.append(
                f"portfolio '{name}': {label} '{item}' has unknown key(s): "
                + ", ".join(f"'{key}'" for key in unknown)
                + "."
            )

        if "target" not in entry:
            errors.append(f"portfolio '{name}': {label} '{item}' is missing 'target'.")
            continue
        try:
            target = parse_pct(entry["target"])
        except (ArithmeticError, ValueError):
            errors.append(
                f"portfolio '{name}': {label} '{item}' has an invalid target "
                f"'{entry['target']}'."
            )
            continue
        if not Decimal(0) <= target <= Decimal(100):
            errors.append(
                f"portfolio '{name}': {label} '{item}' target {target}% "
                "is out of range [0, 100]."
            )
        targets[item] = target
        total += target

    if require_sum and abs(total - Decimal(100)) > SUM_TOLERANCE:
        errors.append(
            f"portfolio '{name}': {label} target allocation sums to {total}%, "
            "expected 100%."
        )

    return targets, bands, errors


def _validate_accounts(name: str, accounts: Any, errors: list[str]) -> list[str]:
    """Validate a portfolio's `accounts`, appending to `errors`.

    The shape is checked, not just the presence. A bare string would be list()-ed into
    one regex per character, each matched unanchored, quietly selecting most of the
    ledger; an account written without quotes but ending in a colon parses as a mapping,
    which is the foot-gun the documentation warns about. Caught here, both get a message
    instead of a wrong report or a TypeError out of `re.compile`.

    Return the accounts to use, empty when they cannot be trusted.

    """
    if not accounts:
        errors.append(f"portfolio '{name}': no 'accounts' defined.")
        return []
    if not isinstance(accounts, list):
        errors.append(f"portfolio '{name}': 'accounts' is not a list.")
        return []
    bad = [
        f"portfolio '{name}': account #{i} is not a string: '{account}'."
        " Quote patterns ending in a colon."
        for i, account in enumerate(accounts, start=1)
        if not isinstance(account, str)
    ]
    errors.extend(bad)
    return [] if bad else list(accounts)


def _validate_portfolio(
    portfolio: Any, index: int, require_sum: bool
) -> tuple[Optional[PortfolioConfig], list[str]]:
    """Validate one raw portfolio, returning ``(config, errors)``.

    `index` is its 1-based position in the file, used to point at one that has no name
    to be called by. `config` is None when the portfolio is too broken to build one;
    `errors` is empty exactly when it is not.

    """
    if not isinstance(portfolio, dict):
        return None, [f"portfolio #{index} is not a mapping."]

    errors: list[str] = []

    name = portfolio.get("name")
    if name is not None and not isinstance(name, str):
        errors.append(f"portfolio #{index}: non-string 'name': '{name}'. Quote it.")
        name = UNNAMED
    elif not name or not name.strip():
        errors.append(f"portfolio #{index}: no 'name' defined.")
        name = UNNAMED

    accounts = _validate_accounts(name, portfolio.get("accounts"), errors)

    try:
        band = own_band(portfolio)
    except AssetAllocationError as exc:
        errors.append(f"portfolio '{name}': {exc.errors[0]}")
        band = Band()

    legacy = [key for key in ALLOC_BLOCKS.values() if portfolio.get(key)]
    if legacy:
        errors.append(
            f"portfolio '{name}': "
            + " and ".join(f"'{key}'" for key in legacy)
            + " must be nested under an 'allocation:' key."
        )

    known = {"name", "accounts", "divergence-threshold", "allocation"}
    unknown = sorted(set(portfolio) - known - set(ALLOC_BLOCKS.values()))
    if unknown:
        errors.append(
            f"portfolio '{name}': unknown key(s): "
            + ", ".join(f"'{key}'" for key in unknown)
            + "."
        )

    allocation = portfolio.get("allocation")
    if allocation is None:
        if not legacy:
            errors.append(f"portfolio '{name}': no 'allocation' defined.")
        return None, errors
    if not isinstance(allocation, dict):
        errors.append(f"portfolio '{name}': 'allocation' is not a mapping.")
        return None, errors
    unknown = sorted(set(allocation) - set(ALLOC_BLOCKS.values()))
    if unknown:
        errors.append(
            f"portfolio '{name}': allocation has unknown key(s): "
            + ", ".join(f"'{key}'" for key in unknown)
            + "."
        )

    commodities = _alloc_entries(portfolio, "commodity")
    classes = _alloc_entries(portfolio, "class")
    if not commodities and not classes:
        errors.append(
            f"portfolio '{name}': allocation defines no 'commodities' or 'classes'."
        )
        return None, errors

    # each block is validated only when present: an absent one is not an empty
    # allocation that fails to sum to 100%, it is simply not configured
    commodity_targets: AmountMap = {}
    commodity_bands: dict[str, Band] = {}
    class_targets: AmountMap = {}
    class_bands: dict[str, Band] = {}
    if commodities:
        commodity_targets, commodity_bands, block_errors = _validate_targets(
            name, commodities, "commodity", require_sum
        )
        errors.extend(block_errors)
    if classes:
        class_targets, class_bands, block_errors = _validate_targets(
            name, classes, "class", require_sum
        )
        errors.extend(block_errors)
    if errors:
        return None, errors

    return (
        PortfolioConfig(
            name=name,
            accounts=list(accounts),
            commodity_targets=commodity_targets,
            class_targets=class_targets,
            divergence_band=band,
            commodity_bands=commodity_bands,
            class_bands=class_bands,
        ),
        [],
    )


def parse_config(raw: Any, require_target_sum: bool = False) -> LoadedConfig:
    """Parse and validate a whole configuration, already loaded from YAML.

    Every portfolio is validated eagerly, so a typo anywhere in the file is reported
    even by a caller that goes on to use only one of them. Raise `AssetAllocationError`
    carrying every message found.

    `require_target_sum` makes a target block that does not sum to 100% an error rather
    than something for the caller to flag; see `target_sum`.

    """
    if not isinstance(raw, dict) or "portfolios" not in raw:
        raise AssetAllocationError("missing top-level 'portfolios' key.")

    portfolios = raw["portfolios"]
    if not portfolios:
        raise AssetAllocationError("no portfolios defined.")
    if not isinstance(portfolios, list):
        raise AssetAllocationError("'portfolios' must be a list of portfolios.")

    # reject duplicate names
    names = [
        p["name"]
        for p in portfolios
        if isinstance(p, dict) and isinstance(p.get("name"), str)
    ]
    dupes = sorted({n for n in names if names.count(n) > 1})
    if dupes:
        raise AssetAllocationError("duplicate portfolio name(s): " + ", ".join(dupes))

    errors: list[str] = []

    # reject unknown keys
    unknown = sorted(
        set(raw) - {"portfolios", "asset-class-key", "divergence-threshold"}
    )
    if unknown:
        errors.append(
            "unknown top-level key(s): "
            + ", ".join(f"'{key}'" for key in unknown)
            + "."
        )

    try:
        default_band = own_band(raw)
    except AssetAllocationError as exc:
        errors.extend(exc.errors)
        default_band = Band()  # unused: `errors` is non-empty, so this raises below

    parsed: list[PortfolioConfig] = []
    for index, portfolio in enumerate(portfolios, start=1):
        config, portfolio_errors = _validate_portfolio(
            portfolio, index, require_target_sum
        )
        errors.extend(portfolio_errors)
        if config is not None:
            parsed.append(config)
    if errors:
        raise AssetAllocationError(errors)

    return LoadedConfig(
        portfolios=parsed,
        # `or` rather than a default: 'asset-class-key:' with nothing after it parses as
        # None, and looking metadata up under None would silently leave every commodity
        # without an asset class, emptying the whole class report
        asset_class_key=raw.get("asset-class-key") or DEFAULT_ASSET_CLASS_KEY,
        default_band=default_band,
    )


def load_config(path: Any, require_target_sum: bool = False) -> LoadedConfig:
    """Load, parse and validate a configuration file.

    Raise `AssetAllocationError` on an unreadable or unparseable file, or on any problem
    `parse_config` finds.

    """
    try:
        with open(path, encoding="utf-8") as f:
            raw = yaml.safe_load(f)
    except OSError as ex:
        raise AssetAllocationError(
            f"cannot read asset allocation configuration file {path}: {ex}"
        ) from ex
    except yaml.YAMLError as ex:
        raise AssetAllocationError(
            f"cannot parse asset allocation configuration file {path}: {ex}"
        ) from ex
    return parse_config(raw, require_target_sum)


def commodity_asset_classes(entries: Iterable[Any], key: str) -> dict[str, str]:
    """Map commodity -> its asset-class metadata value.

    Built from the ledger's Commodity directives, reading metadata key `key`.
    Commodities without that metadata are omitted.

    """
    classes: dict[str, str] = {}
    for entry in entries:
        if isinstance(entry, Commodity):
            value = entry.meta.get(key)
            if value is not None:
                classes[entry.currency] = str(value)
    return classes


def match_class(asset_class: str, targets: Iterable[str]) -> Optional[str]:
    """Return the most-specific configured target matching `asset_class`.

    A target ``T`` matches if ``asset_class == T`` or ``asset_class`` starts with ``T +
    ':'`` (asset classes are hierarchical, ':'-separated). Among all matching targets
    the longest (most specific) one wins. Return None if none matches.

    """
    best = None
    for target in targets:
        if asset_class == target or asset_class.startswith(target + ":"):
            if best is None or len(target) > len(best):
                best = target
    return best


def bucket_commodities(
    values: AmountMap, asset_classes: dict[str, str], class_names: list[str]
) -> tuple[Members, list[tuple[str, Decimal, str]]]:
    """Group held commodities into their most-specific configured asset class.

    Return ``(members, unconfigured)`` where `members` maps each class in `class_names`
    to its ``{commodity: value}`` holdings, and `unconfigured` is a list of
    ``(commodity, value, reason)`` for held commodities that could not be bucketed (no
    asset-class metadata, or a class that is not targeted).  Callers format their own
    warning around each `reason`.

    """
    members: Members = {t: {} for t in class_names}
    unconfigured: list[tuple[str, Decimal, str]] = []
    for commodity, value in values.items():
        asset_class = asset_classes.get(commodity)
        if asset_class is None:
            unconfigured.append((commodity, value, "has no asset-class metadata"))
            continue
        bucket = match_class(asset_class, class_names)
        if bucket is None:
            unconfigured.append(
                (commodity, value, f"asset class '{asset_class}' is not targeted")
            )
            continue
        members[bucket][commodity] = value
    return members, unconfigured


def compile_account_patterns(accounts: list[str]) -> list[re.Pattern]:
    """Compile a portfolio's account regexes, reporting the offending one.

    Matched unanchored, like Beanquery's `~` operator.
    """
    patterns = []
    for account in accounts:
        try:
            patterns.append(re.compile(account))
        except re.error as ex:
            raise AssetAllocationError(
                f"invalid account pattern '{account}': {ex}"
            ) from ex
    return patterns


def apply_residual(
    assignments: list[Assignment], target_total: Decimal
) -> list[Assignment]:
    """Nudge the first assignment so the (cent-rounded) amounts sum exactly.

    Public because splitting a total into rounded parts is needed by any caller building
    trades, not only by the two strategies below.

    `assignments` is a list of ``(commodity, value, amount)`` ordered with the largest
    trade first; the rounding residual against `target_total` is added to that first
    trade.

    """
    if not assignments:
        return assignments
    residual = quantize(target_total) - sum((a for _, _, a in assignments), Decimal(0))
    commodity, value, amount = assignments[0]
    assignments[0] = (commodity, value, amount + residual)
    return assignments


def proportional_split(
    dev_value: Decimal, members: AmountMap, cur_value: Decimal
) -> list[Assignment]:
    """Split a class gap across all members proportional to current value.

    Return a list of ``(commodity, value, amount)`` (largest value first) whose amounts
    sum exactly to `dev_value` (rounded to cents). Each amount carries the sign of
    `dev_value` (positive => sell, negative => buy).

    """
    members_sorted = sorted(members.items(), key=lambda kv: kv[1], reverse=True)
    assignments = [
        (commodity, value, quantize(dev_value * value / cur_value))
        for commodity, value in members_sorted
    ]
    return apply_residual(assignments, dev_value)


def minimal_split(
    dev_value: Decimal,
    members: AmountMap,
    commodity_targets: AmountMap,
    total_value: Decimal,
    thresholds: AmountMap,
    max_trades: Optional[int] = None,
) -> tuple[list[Assignment], Decimal]:
    """Close a class gap using the fewest commodities.

    Greedily allocate ``abs(dev_value)`` to the members with the most tradeable
    *capacity* first; each member's capacity is bounded so the trade does not push its
    own allocation beyond ±threshold of its commodity target (when `commodity_targets`
    lists it; otherwise unbounded). Each commodity's own threshold is looked up in
    `thresholds`, which must therefore cover every commodity `commodity_targets` has a
    target for. Selling is bounded below by ``(target - threshold)`` of the portfolio,
    buying above by ``(target + threshold)``. When `max_trades` is given, at most that
    many commodities are used (the highest-capacity ones), which may increase the
    reported shortfall.

    Return ``(assignments, shortfall)`` where `assignments` is a list of ``(commodity,
    value, amount)`` for the traded commodities only (amounts signed like `dev_value`,
    summing to the covered amount), and `shortfall` is the amount left uncovered when
    capacities cannot reach the full gap.

    """
    selling = dev_value > 0
    gap = abs(dev_value)

    capacities = []
    for commodity, value in members.items():
        target_pct = commodity_targets.get(commodity)
        if selling:
            if target_pct is None:
                floor = Decimal(0)
            else:
                band = (target_pct - thresholds[commodity]) / 100
                floor = max(Decimal(0), band * total_value)
            cap = min(max(value - floor, Decimal(0)), value)
        else:
            if target_pct is None:
                cap = Decimal("Infinity")
            else:
                ceil = (target_pct + thresholds[commodity]) / 100 * total_value
                cap = max(ceil - value, Decimal(0))
        if cap > 0:
            capacities.append((commodity, value, cap))

    # most capacity first => fewest commodities; deterministic tie-breaks
    capacities.sort(key=lambda cvc: (cvc[2], cvc[1], cvc[0]), reverse=True)
    if max_trades is not None:
        capacities = capacities[:max_trades]

    assignments = []
    remaining = gap
    sign = Decimal(1) if selling else Decimal(-1)
    for commodity, value, cap in capacities:
        if remaining <= 0:
            break
        take = min(remaining, cap)
        assignments.append((commodity, value, sign * quantize(take)))
        remaining -= take

    shortfall = max(remaining, Decimal(0))
    if shortfall <= 0:
        # exact reconciliation: absorb cent residual into the largest trade
        assignments = apply_residual(assignments, dev_value)
    return assignments, quantize(shortfall)

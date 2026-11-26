import textwrap
from decimal import Decimal

import pytest
import yaml

from fava_portfolio_returns.api.asset_allocation_core import DEFAULT_BAND
from fava_portfolio_returns.api.asset_allocation_core import AssetAllocationError
from fava_portfolio_returns.api.asset_allocation_core import Band
from fava_portfolio_returns.api.asset_allocation_core import PortfolioConfig
from fava_portfolio_returns.api.asset_allocation_core import bucket_commodities
from fava_portfolio_returns.api.asset_allocation_core import compile_account_patterns
from fava_portfolio_returns.api.asset_allocation_core import match_class
from fava_portfolio_returns.api.asset_allocation_core import minimal_split
from fava_portfolio_returns.api.asset_allocation_core import parse_config
from fava_portfolio_returns.api.asset_allocation_core import parse_pct
from fava_portfolio_returns.api.asset_allocation_core import proportional_split
from fava_portfolio_returns.api.asset_allocation_core import quantize
from fava_portfolio_returns.api.asset_allocation_core import resolve_band
from fava_portfolio_returns.api.asset_allocation_core import resolve_item_thresholds
from fava_portfolio_returns.api.asset_allocation_core import target_sum


def load(text: str, require_target_sum: bool = False):
    return parse_config(yaml.safe_load(textwrap.dedent(text)), require_target_sum)


def test_parse_pct():
    assert parse_pct("25%") == Decimal("25")
    assert parse_pct("25") == Decimal("25")
    assert parse_pct(25) == Decimal("25")


@pytest.mark.parametrize(
    "value", [float("nan"), "nan", "NaN%", float("inf"), "-Infinity"]
)
def test_parse_pct_rejects_non_finite(value):
    with pytest.raises(ValueError):
        parse_pct(value)


def test_quantize_rounds_to_cents_half_even():
    assert quantize(Decimal("1.005")) == Decimal("1.00")
    assert quantize(Decimal("1.015")) == Decimal("1.02")


def test_target_sum():
    assert target_sum({"A": Decimal("60"), "B": Decimal("40")}) == (
        Decimal("100"),
        True,
    )
    assert target_sum({"A": Decimal("60"), "B": Decimal("30")}) == (
        Decimal("90"),
        False,
    )
    # within SUM_TOLERANCE
    assert target_sum({"A": Decimal("99.95")})[1] is True


def test_band_merge_fills_sides_in():
    outer = Band(of_portfolio=Decimal("5"), of_target=Decimal("25"))
    # a band that tightens only one side keeps inheriting the other
    assert Band(of_target=Decimal("10")).merge(outer) == Band(
        Decimal("5"), Decimal("10")
    )
    assert Band(of_portfolio=Decimal("3")).merge(outer) == Band(
        Decimal("3"), Decimal("25")
    )
    assert Band().merge(outer) == outer


def test_band_width_takes_the_smaller_side():
    band = Band(of_portfolio=Decimal("5"), of_target=Decimal("25"))
    # on a large target the absolute cap binds, on a small one the relative one
    assert band.width(Decimal("60")) == Decimal("5")
    assert band.width(Decimal("5")) == Decimal("1.25")
    assert band.width(Decimal("20")) == Decimal("5")  # the two meet here


def test_band_width_with_one_side_unset():
    assert Band(of_portfolio=Decimal("5")).width(Decimal("4")) == Decimal("5")
    assert Band(of_target=Decimal("25")).width(Decimal("4")) == Decimal("1")


def test_all_unset_band_is_refused_not_treated_as_uncapped():
    """The one answer that would let a target drift unwatched in silence."""
    with pytest.raises(AssetAllocationError, match="neither side set"):
        Band().width(Decimal("10"))
    with pytest.raises(AssetAllocationError, match="neither side set"):
        Band().describe()


def test_band_describe():
    assert DEFAULT_BAND.describe() == "min(5% of portfolio, 25% of target)"
    assert Band(of_portfolio=Decimal("3")).describe() == "3% of portfolio"
    assert Band(of_target=Decimal("10")).describe() == "10% of target"


VALID = """\
    asset-class-key: my-class
    divergence-threshold:
      of-portfolio: 7%
      of-target: 30%
    portfolios:
      - name: p1
        accounts:
          - "Assets:Broker:"
        divergence-threshold:
          of-portfolio: 3%
        allocation:
          commodities:
            - commodity: AAA
              target: 60%
              divergence-threshold:
                of-target: 10%
            - commodity: BBB
              target: 40%
          classes:
            - asset-class: stocks
              target: 60%
            - asset-class: bonds
              target: 40%
"""


def test_parse_config_valid():
    config = load(VALID, require_target_sum=True)
    assert config.asset_class_key == "my-class"
    assert config.default_band == Band(Decimal("7"), Decimal("30"))
    [portfolio] = config.portfolios
    assert portfolio.name == "p1"
    assert portfolio.accounts == ["Assets:Broker:"]
    assert portfolio.commodity_targets == {"AAA": Decimal("60"), "BBB": Decimal("40")}
    assert portfolio.class_targets == {"stocks": Decimal("60"), "bonds": Decimal("40")}
    assert portfolio.divergence_band == Band(of_portfolio=Decimal("3"))
    assert portfolio.commodity_bands == {"AAA": Band(of_target=Decimal("10"))}
    assert portfolio.class_bands == {}


def test_parse_config_defaults():
    config = load(
        """\
        portfolios:
          - name: p1
            accounts: ["Assets:Broker:"]
            allocation:
              commodities:
                - commodity: AAA
                  target: 100%
    """
    )
    assert config.asset_class_key == "asset-class"
    assert config.default_band == Band()
    assert config.portfolios[0].divergence_band == Band()


def test_portfolio_config_accessors():
    portfolio = load(VALID).portfolios[0]
    assert portfolio.targets("commodity") == portfolio.commodity_targets
    assert portfolio.targets("class") == portfolio.class_targets
    assert portfolio.bands("commodity") == portfolio.commodity_bands
    assert portfolio.bands("class") == portfolio.class_bands


# One row per way a configuration can be wrong, each pinning the exact messages.
# This table is the point of the module: both consumers of it report a broken
# configuration identically, and adding a case here is how that stays true.
BAD_CONFIGS = {
    "band_empty": (
        """\
        portfolios:
          - name: p1
            accounts: ["Assets:X"]
            allocation:
              commodities:
                - commodity: AAA
                  target: 100%
                  divergence-threshold: {}
        """,
        [
            "portfolio 'p1': commodity 'AAA': empty divergence-threshold; "
            "set 'of-portfolio' and/or 'of-target' to a percentage."
        ],
    ),
    # a side written with no value after it is just as empty, and used to slip
    # through as a band that silently did nothing
    "band_null_side": (
        """\
        portfolios:
          - name: p1
            accounts: ["Assets:X"]
            divergence-threshold:
              of-portfolio:
            allocation:
              commodities:
                - commodity: AAA
                  target: 100%
        """,
        [
            "portfolio 'p1': empty divergence-threshold; set 'of-portfolio' and/or 'of-target' to a percentage."
        ],
    ),
    "band_scalar": (
        """\
        portfolios:
          - name: p1
            accounts: ["Assets:X"]
            divergence-threshold: 3%
            allocation:
              commodities:
                - commodity: AAA
                  target: 100%
        """,
        [
            "portfolio 'p1': divergence-threshold must be a mapping of 'of-portfolio' and/or 'of-target', not '3%'."
        ],
    ),
    "band_unknown_key": (
        """\
        portfolios:
          - name: p1
            accounts: ["Assets:X"]
            divergence-threshold:
              of-portfolios: 3%
            allocation:
              commodities:
                - commodity: AAA
                  target: 100%
        """,
        [
            "portfolio 'p1': unknown divergence-threshold key(s) 'of-portfolios'; "
            "expected 'of-portfolio' and/or 'of-target'."
        ],
    ),
    "band_out_of_range": (
        """\
        portfolios:
          - name: p1
            accounts: ["Assets:X"]
            divergence-threshold:
              of-target: 150%
            allocation:
              commodities:
                - commodity: AAA
                  target: 100%
        """,
        [
            "portfolio 'p1': divergence-threshold of-target 150% is out of range [0, 100]."
        ],
    ),
    "band_invalid": (
        """\
        portfolios:
          - name: p1
            accounts: ["Assets:X"]
            divergence-threshold:
              of-portfolio: abc
            allocation:
              commodities:
                - commodity: AAA
                  target: 100%
        """,
        ["portfolio 'p1': invalid divergence-threshold of-portfolio 'abc'."],
    ),
    # a half-migrated portfolio: the stray block used to be dropped in silence
    "legacy_alongside_allocation": (
        """\
        portfolios:
          - name: p1
            accounts: ["Assets:X"]
            commodities:
              - commodity: ZZZ
                target: 100%
            allocation:
              commodities:
                - commodity: AAA
                  target: 100%
        """,
        ["portfolio 'p1': 'commodities' must be nested under an 'allocation:' key."],
    ),
    # pins the order: the band is reported before the target, then the sum
    "bad_band_and_bad_target": (
        """\
        portfolios:
          - name: p1
            accounts: ["Assets:X"]
            allocation:
              commodities:
                - commodity: AAA
                  target: nope
                  divergence-threshold: 5%
        """,
        [
            "portfolio 'p1': commodity 'AAA': divergence-threshold must be a mapping of "
            "'of-portfolio' and/or 'of-target', not '5%'.",
            "portfolio 'p1': commodity 'AAA' has an invalid target 'nope'.",
            "portfolio 'p1': commodity target allocation sums to 0%, expected 100%.",
        ],
    ),
    "targets_not_a_list": (
        """\
        portfolios:
          - name: p1
            accounts: ["Assets:X"]
            allocation:
              commodities:
                AAA: 100%
        """,
        [
            "portfolio 'p1': commodity #1 is not a mapping.",
            "portfolio 'p1': commodity target allocation sums to 0%, expected 100%.",
        ],
    ),
    "allocation_not_a_mapping": (
        """\
        portfolios:
          - name: p1
            accounts: ["Assets:X"]
            allocation:
              - AAA
        """,
        ["portfolio 'p1': 'allocation' is not a mapping."],
    ),
    "portfolios_empty": ("portfolios: []\n", ["no portfolios defined."]),
    "portfolios_key_missing": ("foo: bar\n", ["missing top-level 'portfolios' key."]),
    "duplicate_portfolio_names": (
        """\
        portfolios:
          - name: p1
            accounts: ["Assets:X"]
            allocation: {commodities: [{commodity: AAA, target: 100%}]}
          - name: p1
            accounts: ["Assets:Y"]
            allocation: {commodities: [{commodity: BBB, target: 100%}]}
        """,
        ["duplicate portfolio name(s): p1"],
    ),
    "unknown_portfolio_key": (
        """\
        portfolios:
          - name: p1
            accounts: ["Assets:X"]
            divergence-treshold: {of-portfolio: 3%}
            allocation: {commodities: [{commodity: AAA, target: 100%}]}
        """,
        ["portfolio 'p1': unknown key(s): 'divergence-treshold'."],
    ),
    "unknown_target_key": (
        """\
        portfolios:
          - name: p1
            accounts: ["Assets:X"]
            allocation: {commodities: [{commodity: AAA, target: 100%, targt: 5%}]}
        """,
        ["portfolio 'p1': commodity 'AAA' has unknown key(s): 'targt'."],
    ),
    "no_accounts": (
        """\
        portfolios:
          - name: p1
            allocation: {commodities: [{commodity: AAA, target: 100%}]}
        """,
        ["portfolio 'p1': no 'accounts' defined."],
    ),
    # a bare string would become one regex per character, each matched
    # unanchored, and so would select most of the ledger without a word
    "accounts_not_a_list": (
        """\
        portfolios:
          - name: p1
            accounts: "Assets:X"
            allocation: {commodities: [{commodity: AAA, target: 100%}]}
        """,
        ["portfolio 'p1': 'accounts' is not a list."],
    ),
    # the documented foot-gun: unquoted and ending in a colon, so YAML makes it
    # a mapping. Used to escape re.compile as a TypeError.
    "account_not_a_string": (
        """\
        portfolios:
          - name: p1
            accounts:
              - Assets:Broker:
            allocation: {commodities: [{commodity: AAA, target: 100%}]}
        """,
        [
            "portfolio 'p1': account #1 is not a string: '{'Assets:Broker': None}'. Quote patterns ending in a colon."
        ],
    ),
    # a name selects a portfolio, titles its report and keys it in the
    # frontend, so a nameless one is indistinguishable in all three
    "no_name": (
        """\
        portfolios:
          - accounts: ["Assets:X"]
            allocation: {commodities: [{commodity: AAA, target: 100%}]}
        """,
        ["portfolio #1: no 'name' defined."],
    ),
    "blank_name": (
        """\
        portfolios:
          - name: "  "
            accounts: ["Assets:X"]
            allocation: {commodities: [{commodity: AAA, target: 100%}]}
        """,
        ["portfolio #1: no 'name' defined."],
    ),
    # present but empty: reads as an intent to set a band, and inheriting
    # silently is the failure an empty mapping is already rejected for
    "band_empty_body": (
        """\
        portfolios:
          - name: p1
            accounts: ["Assets:X"]
            divergence-threshold:
            allocation: {commodities: [{commodity: AAA, target: 100%}]}
        """,
        [
            "portfolio 'p1': empty divergence-threshold; set 'of-portfolio' and/or 'of-target' to a percentage."
        ],
    ),
    "unknown_top_level_key": (
        """\
        asset-class-keys: my-class
        divergence-treshold: {of-portfolio: 1%}
        portfolios:
          - name: p1
            accounts: ["Assets:X"]
            allocation: {commodities: [{commodity: AAA, target: 100%}]}
        """,
        ["unknown top-level key(s): 'asset-class-keys', 'divergence-treshold'."],
    ),
    # an unquoted 007 parses as an int, matches no holding, and would sit in
    # the report as a permanent 0%
    "non_string_commodity": (
        """\
        portfolios:
          - name: p1
            accounts: ["Assets:X"]
            allocation: {commodities: [{commodity: 007, target: 100%}]}
        """,
        [
            "portfolio 'p1': commodity #1 has a non-string 'commodity': '7'. Quote it.",
            "portfolio 'p1': commodity target allocation sums to 0%, expected 100%.",
        ],
    ),
    "no_allocation": (
        """\
        portfolios:
          - name: p1
            accounts: ["Assets:X"]
        """,
        ["portfolio 'p1': no 'allocation' defined."],
    ),
    "empty_allocation": (
        """\
        portfolios:
          - name: p1
            accounts: ["Assets:X"]
            allocation: {}
        """,
        ["portfolio 'p1': allocation defines no 'commodities' or 'classes'."],
    ),
    # the duplicate is the error; both entries still count toward the sum, so
    # that a bogus total does not point at the wrong thing
    "duplicate_commodity": (
        """\
        portfolios:
          - name: p1
            accounts: ["Assets:X"]
            allocation:
              commodities:
                - commodity: AAA
                  target: 50%
                - commodity: AAA
                  target: 50%
        """,
        ["portfolio 'p1': duplicate commodity 'AAA'."],
    ),
    "target_out_of_range": (
        """\
        portfolios:
          - name: p1
            accounts: ["Assets:X"]
            allocation: {classes: [{asset-class: stocks, target: 150%}]}
        """,
        [
            "portfolio 'p1': class 'stocks' target 150% is out of range [0, 100].",
            "portfolio 'p1': class target allocation sums to 150%, expected 100%.",
        ],
    ),
    "target_missing": (
        """\
        portfolios:
          - name: p1
            accounts: ["Assets:X"]
            allocation: {commodities: [{commodity: AAA}]}
        """,
        [
            "portfolio 'p1': commodity 'AAA' is missing 'target'.",
            "portfolio 'p1': commodity target allocation sums to 0%, expected 100%.",
        ],
    ),
    "item_key_missing": (
        """\
        portfolios:
          - name: p1
            accounts: ["Assets:X"]
            allocation: {commodities: [{target: 100%}]}
        """,
        [
            "portfolio 'p1': commodity #1 is missing 'commodity'.",
            "portfolio 'p1': commodity target allocation sums to 0%, expected 100%.",
        ],
    ),
    # a misspelled block name used to be ignored, dropping its report silently
    "allocation_unknown_key": (
        """\
        portfolios:
          - name: p1
            accounts: ["Assets:X"]
            allocation:
              commodities: [{commodity: AAA, target: 100%}]
              clases: [{asset-class: stocks, target: 100%}]
        """,
        ["portfolio 'p1': allocation has unknown key(s): 'clases'."],
    ),
    # NaN used to escape as a raw decimal.InvalidOperation from the range check
    "target_nan": (
        """\
        portfolios:
          - name: p1
            accounts: ["Assets:X"]
            allocation: {commodities: [{commodity: AAA, target: .nan}]}
        """,
        [
            "portfolio 'p1': commodity 'AAA' has an invalid target 'nan'.",
            "portfolio 'p1': commodity target allocation sums to 0%, expected 100%.",
        ],
    ),
    "band_nan": (
        """\
        portfolios:
          - name: p1
            accounts: ["Assets:X"]
            divergence-threshold: {of-target: "nan%"}
            allocation: {commodities: [{commodity: AAA, target: 100%}]}
        """,
        ["portfolio 'p1': invalid divergence-threshold of-target 'nan%'."],
    ),
    # non-string names used to crash the duplicate check (TypeError when
    # joining ints) before validation ran, or be reported as missing
    "name_duplicate_int": (
        """\
        portfolios:
          - name: 2024
            accounts: ["Assets:X"]
            allocation: {commodities: [{commodity: AAA, target: 100%}]}
          - name: 2024
            accounts: ["Assets:Y"]
            allocation: {commodities: [{commodity: AAA, target: 100%}]}
        """,
        [
            "portfolio #1: non-string 'name': '2024'. Quote it.",
            "portfolio #2: non-string 'name': '2024'. Quote it.",
        ],
    ),
    "name_list": (
        """\
        portfolios:
          - name: [a, b]
            accounts: ["Assets:X"]
            allocation: {commodities: [{commodity: AAA, target: 100%}]}
        """,
        ["portfolio #1: non-string 'name': '['a', 'b']'. Quote it."],
    ),
}


@pytest.mark.parametrize("case", sorted(BAD_CONFIGS))
def test_rejected_configs_report_exactly(case):
    text, expected = BAD_CONFIGS[case]
    with pytest.raises(AssetAllocationError) as excinfo:
        load(text, require_target_sum=True)
    assert excinfo.value.errors == expected


def test_asset_class_key_written_without_a_value_falls_back():
    """Otherwise metadata is looked up under None and every class report empties."""
    config = load(
        """\
        asset-class-key:
        portfolios:
          - name: p1
            accounts: ["Assets:X"]
            allocation: {commodities: [{commodity: AAA, target: 100%}]}
    """
    )
    assert config.asset_class_key == "asset-class"


def test_target_sum_is_not_an_error_by_default():
    """The sum is an error only for callers that must refuse to act on it."""
    text = """\
        portfolios:
          - name: p1
            accounts: ["Assets:X"]
            allocation: {commodities: [{commodity: AAA, target: 60%}]}
    """
    [portfolio] = load(text).portfolios  # accepted
    assert target_sum(portfolio.commodity_targets) == (Decimal("60"), False)
    with pytest.raises(AssetAllocationError, match="sums to 60%"):
        load(text, require_target_sum=True)


def test_every_portfolio_is_validated_not_just_the_first():
    """A typo in a portfolio the caller never selects is still reported."""
    with pytest.raises(AssetAllocationError) as excinfo:
        load(
            """\
            portfolios:
              - name: good
                accounts: ["Assets:X"]
                allocation: {commodities: [{commodity: AAA, target: 100%}]}
              - name: bad
                accounts: ["Assets:Y"]
                allocation: {commodities: [{commodity: BBB, target: 100%, oops: 1}]}
        """
        )
    assert excinfo.value.errors == [
        "portfolio 'bad': commodity 'BBB' has unknown key(s): 'oops'."
    ]


def test_errors_accumulate_across_portfolios():
    with pytest.raises(AssetAllocationError) as excinfo:
        load(
            """\
            portfolios:
              - name: p1
                allocation: {commodities: [{commodity: AAA, target: 100%}]}
              - name: p2
                allocation: {commodities: [{commodity: BBB, target: 100%}]}
        """
        )
    assert excinfo.value.errors == [
        "portfolio 'p1': no 'accounts' defined.",
        "portfolio 'p2': no 'accounts' defined.",
    ]


def test_unnamed_portfolio_is_still_identifiable_in_later_messages():
    """A missing name is an error, but must not make the rest unattributable."""
    with pytest.raises(AssetAllocationError) as excinfo:
        load(
            """\
            portfolios:
              - accounts: ["Assets:X"]
        """
        )
    assert excinfo.value.errors == [
        "portfolio #1: no 'name' defined.",
        "portfolio '<unnamed>': no 'allocation' defined.",
    ]


def test_two_nameless_portfolios_are_both_reported():
    """They used to collapse to one '<unnamed>' and pass the duplicate check."""
    with pytest.raises(AssetAllocationError) as excinfo:
        load(
            """\
            portfolios:
              - accounts: ["Assets:X"]
                allocation: {commodities: [{commodity: AAA, target: 100%}]}
              - accounts: ["Assets:Y"]
                allocation: {commodities: [{commodity: BBB, target: 100%}]}
        """
        )
    assert excinfo.value.errors == [
        "portfolio #1: no 'name' defined.",
        "portfolio #2: no 'name' defined.",
    ]


def test_resolve_band_precedence():
    portfolio = PortfolioConfig(
        name="p", accounts=[], divergence_band=Band(of_portfolio=Decimal("3"))
    )
    # the portfolio's side wins, the unset one falls through to the file, and
    # the file's unset side falls through to the built-in 5/25
    assert resolve_band(portfolio, Band(of_portfolio=Decimal("15"))) == Band(
        Decimal("3"), Decimal("25")
    )
    assert resolve_band(portfolio, Band(of_target=Decimal("10"))) == Band(
        Decimal("3"), Decimal("10")
    )
    assert resolve_band(PortfolioConfig(name="p", accounts=[]), Band()) == DEFAULT_BAND


def test_resolve_item_thresholds_derives_from_each_target():
    portfolio = PortfolioConfig(
        name="p",
        accounts=[],
        commodity_targets={"BIG": Decimal("60"), "SMALL": Decimal("8")},
        commodity_bands={"SMALL": Band(of_target=Decimal("50"))},
    )
    band = resolve_band(portfolio, Band())
    thresholds = resolve_item_thresholds(portfolio, "commodity", band)
    # BIG: min(5pp, 25% of 60) = 5pp; SMALL overrides only the relative side,
    # so min(5pp, 50% of 8) = 4pp
    assert thresholds == {"BIG": Decimal("5"), "SMALL": Decimal("4")}


def test_match_class_hierarchical():
    targets = ["stocks", "stocks:health", "bonds"]
    assert match_class("stocks", targets) == "stocks"
    assert (
        match_class("stocks:health", targets) == "stocks:health"
    )  # most specific wins
    assert match_class("stocks:world", targets) == "stocks"  # falls back to parent
    assert match_class("cash", targets) is None


def test_bucket_commodities():
    values = {"AAA": Decimal("10"), "BBB": Decimal("20"), "CCC": Decimal("30")}
    classes = {"AAA": "stocks:world", "BBB": "cash"}
    members, unconfigured = bucket_commodities(values, classes, ["stocks", "bonds"])
    assert members == {"stocks": {"AAA": Decimal("10")}, "bonds": {}}
    assert unconfigured == [
        ("BBB", Decimal("20"), "asset class 'cash' is not targeted"),
        ("CCC", Decimal("30"), "has no asset-class metadata"),
    ]


def test_compile_account_patterns():
    assert len(compile_account_patterns(["Assets:A", "Assets:B"])) == 2
    with pytest.raises(AssetAllocationError, match="invalid account pattern"):
        compile_account_patterns(["Assets:[Broker"])


def test_proportional_split_sums_exactly():
    members = {"AAA": Decimal("70"), "BBB": Decimal("30")}
    shares = proportional_split(Decimal("10.00"), members, Decimal("100"))
    assert sum(amount for _, _, amount in shares) == Decimal("10.00")
    assert shares[0][0] == "AAA"  # largest holding first


def test_minimal_split_respects_capacity_and_reports_shortfall():
    members = {"AAA": Decimal("70"), "BBB": Decimal("30")}
    commodity_targets = {"AAA": Decimal("65"), "BBB": Decimal("35")}
    five = {"AAA": Decimal("5"), "BBB": Decimal("5")}
    # sell 10 from a 100 total; AAA capacity down to (65-5)% = 60 => 10 capacity
    assignments, shortfall = minimal_split(
        Decimal("10"), members, commodity_targets, Decimal("100"), five
    )
    assert shortfall == Decimal("0.00")
    assert sum(a for _, _, a in assignments) == Decimal("10.00")

    # tiny capacities => cannot cover the whole gap
    tight = {"AAA": Decimal("66"), "BBB": Decimal("34")}
    _assignments, shortfall = minimal_split(
        Decimal("20"), members, tight, Decimal("100"), five
    )
    assert shortfall > Decimal("0")


def test_minimal_split_per_commodity_threshold():
    members = {"AAA": Decimal("70"), "BBB": Decimal("30")}
    commodity_targets = {"AAA": Decimal("65"), "BBB": Decimal("35")}
    # AAA's own threshold is tighter (2pp): it can only be sold down to 63,
    # i.e. a capacity of 7 against the gap of 10, where 5pp allowed the full 10.
    # BBB is already under its own floor (30 at 5pp), so it cannot take the rest.
    thresholds = {"AAA": Decimal("2"), "BBB": Decimal("5")}
    assignments, shortfall = minimal_split(
        Decimal("10"), members, commodity_targets, Decimal("100"), thresholds
    )
    assert [(c, a) for c, _, a in assignments] == [("AAA", Decimal("7.00"))]
    assert shortfall == Decimal("3.00")


def test_minimal_split_max_trades_caps_the_commodities_used():
    members = {"AAA": Decimal("50"), "BBB": Decimal("30"), "CCC": Decimal("20")}
    assignments, _shortfall = minimal_split(
        Decimal("10"), members, {}, Decimal("100"), {}, max_trades=1
    )
    assert len(assignments) == 1

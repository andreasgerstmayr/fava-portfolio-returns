from decimal import Decimal

import pytest
from beancount import loader
from beancount.core import prices
from beancount.core.data import Commodity
from fava.helpers import FavaAPIError

from fava_portfolio_returns.api.asset_allocation import asset_allocation_report
from fava_portfolio_returns.api.asset_allocation import load_asset_allocation_config
from fava_portfolio_returns.api.asset_allocation_core import Band
from fava_portfolio_returns.api.asset_allocation_core import PortfolioConfig
from fava_portfolio_returns.api.asset_allocation_core import commodity_asset_classes
from fava_portfolio_returns.core.pricer import Pricer

LEDGER = """
option "operating_currency" "USD"

2020-01-01 open Assets:Broker:AAA
2020-01-01 open Assets:Broker:BBB
2020-01-01 open Assets:Cash

2020-01-01 commodity AAA
  name: "Fund AAA"
  asset-class: "stocks"

2020-01-01 commodity BBB
  asset-class: "bonds"

2020-01-01 * "buy AAA"
  Assets:Broker:AAA  10 AAA {10 USD}
  Assets:Cash

2020-01-01 * "buy BBB"
  Assets:Broker:BBB  10 BBB {10 USD}
  Assets:Cash

2021-01-01 price AAA  12 USD
2021-01-01 price BBB   8 USD
"""


def _load():
    entries, errors, _options = loader.load_string(LEDGER)
    assert not errors, errors
    pricer = Pricer(prices.build_price_map(entries))
    names = {
        e.currency: e.meta["name"]
        for e in entries
        if isinstance(e, Commodity) and e.meta.get("name")
    }
    return entries, pricer, names


def build_report(
    commodity_targets=None,
    class_targets=None,
    default_band=Band(),
    accounts=None,
    minimize=False,
    portfolio_band=Band(),
    commodity_bands=None,
    class_bands=None,
):
    entries, pricer, names = _load()
    config = PortfolioConfig(
        name="test",
        accounts=accounts or ["Assets:Broker:"],
        commodity_targets=commodity_targets or {},
        class_targets=class_targets or {},
        divergence_band=portfolio_band,
        commodity_bands=commodity_bands or {},
        class_bands=class_bands or {},
    )
    reports = asset_allocation_report(
        entries,
        pricer,
        [config],
        "USD",
        entries[-1].date,
        default_band,
        asset_classes=commodity_asset_classes(entries, "asset-class"),
        names=names,
        minimize=minimize,
    )
    return reports[0]


def test_load_config_reports_the_first_problem_as_a_fava_error(tmp_path):
    config_file = tmp_path / "asset-allocation.yaml"
    config_file.write_text('portfolios:\n  - name: p1\n    accounts: ["Assets:X"]\n')
    with pytest.raises(FavaAPIError, match="no 'allocation' defined"):
        load_asset_allocation_config(config_file)


def test_load_config_unreadable_file(tmp_path):
    with pytest.raises(FavaAPIError, match="cannot read"):
        load_asset_allocation_config(tmp_path / "nope.yaml")


def test_load_config_valid(tmp_path):
    config_file = tmp_path / "asset-allocation.yaml"
    config_file.write_text(
        """
asset-class-key: my-class
portfolios:
  - name: p1
    accounts:
      - "Assets:Broker:"
    allocation:
      commodities:
        - commodity: AAA
          target: 100%
"""
    )
    config = load_asset_allocation_config(config_file)
    assert config.asset_class_key == "my-class"
    assert config.portfolios[0].commodity_targets == {"AAA": Decimal("100")}


def test_load_config_tolerates_a_target_sum_that_is_not_100(tmp_path):
    """The frontend flags it; unlike a CLI, the report still renders."""
    config_file = tmp_path / "asset-allocation.yaml"
    config_file.write_text(
        """
portfolios:
  - name: p1
    accounts: ["Assets:Broker:"]
    allocation:
      commodities:
        - commodity: AAA
          target: 60%
"""
    )
    assert load_asset_allocation_config(config_file).portfolios[
        0
    ].commodity_targets == {"AAA": Decimal("60")}


def test_invalid_account_pattern_raises_fava_error():
    with pytest.raises(FavaAPIError, match="invalid account pattern"):
        build_report(
            commodity_targets={"AAA": Decimal("100")}, accounts=["Assets:[Broker"]
        )


def test_commodity_report_allocation_and_deviation():
    report = build_report(
        commodity_targets={"AAA": Decimal("50"), "BBB": Decimal("50")}
    )

    assert report["totalValue"] == Decimal("200")  # 10*12 + 10*8
    assert report["classReport"] is None
    commodity = report["commodityReport"]
    assert commodity["diverged"] is True  # +/-10pp > 5pp threshold
    assert commodity["targetSumOk"] is True

    by_commodity = {a["commodity"]: a for a in commodity["assets"]}
    aaa = by_commodity["AAA"]
    assert aaa["name"] == "Fund AAA"
    assert aaa["value"] == Decimal("120")
    assert aaa["currentPct"] == Decimal("60")
    assert aaa["devPct"] == Decimal("10")
    assert aaa["devValue"] == Decimal("20")  # overweight => sell 20
    assert aaa["over"] is True

    bbb = by_commodity["BBB"]
    assert bbb["value"] == Decimal("80")
    assert bbb["devValue"] == Decimal("-20")  # underweight => buy 20


def test_commodity_report_unconfigured():
    # only AAA is configured; BBB is held but not in the target allocation
    report = build_report(commodity_targets={"AAA": Decimal("100")})
    unconfigured = report["commodityReport"]["unconfigured"]
    assert [u["commodity"] for u in unconfigured] == ["BBB"]
    assert unconfigured[0]["value"] == Decimal("80")


def test_commodity_report_within_threshold():
    report = build_report(
        commodity_targets={"AAA": Decimal("60"), "BBB": Decimal("40")}
    )
    assert report["commodityReport"]["diverged"] is False


def test_default_band_is_derived_per_target():
    # the built-in 5/25 rule; above a 20% target the absolute cap is the
    # smaller of the two, so both of these band at 5pp
    report = build_report(
        commodity_targets={"AAA": Decimal("60"), "BBB": Decimal("40")}
    )
    assert report["band"] == {"ofPortfolio": Decimal("5"), "ofTarget": Decimal("25")}
    assert {a["thresholdPct"] for a in report["commodityReport"]["assets"]} == {
        Decimal("5")
    }

    # below a 20% target the relative side is the smaller one: 25% of 8% = 2pp
    report = build_report(commodity_targets={"AAA": Decimal("92"), "BBB": Decimal("8")})
    by_commodity = {a["commodity"]: a for a in report["commodityReport"]["assets"]}
    assert by_commodity["AAA"]["thresholdPct"] == Decimal("5")
    assert by_commodity["BBB"]["thresholdPct"] == Decimal("2")


def test_band_precedence():
    # AAA/BBB are 60/40 against a 50/50 target, i.e. ±10pp off; at those
    # targets the absolute side binds, so of-portfolio is what decides
    targets = {"AAA": Decimal("50"), "BBB": Decimal("50")}

    # the file-level band applies when the portfolio sets none
    report = build_report(
        commodity_targets=targets, default_band=Band(of_portfolio=Decimal("15"))
    )
    assert report["band"] == {"ofPortfolio": Decimal("15"), "ofTarget": Decimal("25")}
    assert report["commodityReport"]["diverged"] is False

    # the portfolio's own side wins over the file-level one
    report = build_report(
        commodity_targets=targets,
        default_band=Band(of_portfolio=Decimal("15")),
        portfolio_band=Band(of_portfolio=Decimal("5")),
    )
    assert report["band"] == {"ofPortfolio": Decimal("5"), "ofTarget": Decimal("25")}
    assert report["commodityReport"]["diverged"] is True

    # the two sides resolve separately: the portfolio tightens only the
    # relative one and keeps inheriting the file's absolute cap
    report = build_report(
        commodity_targets=targets,
        default_band=Band(of_portfolio=Decimal("15")),
        portfolio_band=Band(of_target=Decimal("10")),
    )
    assert report["band"] == {"ofPortfolio": Decimal("15"), "ofTarget": Decimal("10")}
    # min(15pp, 10% of 50%) = 5pp, so the ±10pp deviation is flagged
    assert {a["thresholdPct"] for a in report["commodityReport"]["assets"]} == {
        Decimal("5")
    }
    assert report["commodityReport"]["diverged"] is True


def test_target_band_precedence():
    # AAA/BBB are 60/40 against a 50/50 target, i.e. ±10pp off
    targets = {"AAA": Decimal("50"), "BBB": Decimal("50")}

    # a target's own band is laid over the portfolio's, for that target alone
    report = build_report(
        commodity_targets=targets,
        default_band=Band(of_portfolio=Decimal("15"), of_target=Decimal("100")),
        commodity_bands={"AAA": Band(of_portfolio=Decimal("5"))},
    )
    assert report["band"] == {"ofPortfolio": Decimal("15"), "ofTarget": Decimal("100")}
    commodity = report["commodityReport"]
    by_commodity = {a["commodity"]: a for a in commodity["assets"]}
    assert by_commodity["AAA"]["thresholdPct"] == Decimal("5")
    assert by_commodity["AAA"]["over"] is True  # +10pp beyond its own 5pp
    assert by_commodity["BBB"]["thresholdPct"] == Decimal("15")
    assert by_commodity["BBB"]["over"] is False  # -10pp within the portfolio's 15pp
    assert commodity["diverged"] is True


def test_class_report_target_band():
    # stocks 60% / bonds 40% held against a 50/50 target, i.e. ±10pp off
    report = build_report(
        class_targets={"stocks": Decimal("50"), "bonds": Decimal("50")},
        default_band=Band(of_portfolio=Decimal("15"), of_target=Decimal("100")),
        class_bands={"stocks": Band(of_portfolio=Decimal("5"))},
    )
    by_class = {c["assetClass"]: c for c in report["classReport"]["classes"]}
    assert by_class["stocks"]["thresholdPct"] == Decimal("5")
    assert by_class["stocks"]["over"] is True
    assert by_class["bonds"]["thresholdPct"] == Decimal("15")
    assert by_class["bonds"]["over"] is False


def test_commodity_report_target_sum_validation():
    report = build_report(
        commodity_targets={"AAA": Decimal("50"), "BBB": Decimal("30")}
    )
    commodity = report["commodityReport"]
    assert commodity["targetSum"] == Decimal("80")
    assert commodity["targetSumOk"] is False


def test_class_report_bucketing_and_deviation():
    # AAA (stocks) = 120, BBB (bonds) = 80, total 200
    report = build_report(
        class_targets={"stocks": Decimal("50"), "bonds": Decimal("50")}
    )
    assert report["commodityReport"] is None
    class_report = report["classReport"]
    assert class_report["diverged"] is True

    by_class = {c["assetClass"]: c for c in class_report["classes"]}
    stocks = by_class["stocks"]
    assert stocks["value"] == Decimal("120")
    assert stocks["currentPct"] == Decimal("60")
    assert stocks["devValue"] == Decimal("20")  # overweight => sell 20
    # single member: whole class trade lands on AAA
    assert [(m["commodity"], m["tradeValue"]) for m in stocks["members"]] == [
        ("AAA", Decimal("20"))
    ]

    bonds = by_class["bonds"]
    assert bonds["devValue"] == Decimal("-20")
    assert [(m["commodity"], m["tradeValue"]) for m in bonds["members"]] == [
        ("BBB", Decimal("-20"))
    ]


def test_class_report_unconfigured():
    # bonds class not configured, so BBB has no targeted class
    report = build_report(class_targets={"stocks": Decimal("100")})
    unconfigured = report["classReport"]["unconfigured"]
    assert [u["commodity"] for u in unconfigured] == ["BBB"]
    assert "not targeted" in unconfigured[0]["reason"]


def test_both_reports_present():
    report = build_report(
        commodity_targets={"AAA": Decimal("60"), "BBB": Decimal("40")},
        class_targets={"stocks": Decimal("60"), "bonds": Decimal("40")},
    )
    assert report["commodityReport"] is not None
    assert report["classReport"] is not None


CASH_LEDGER = """
option "operating_currency" "USD"
option "operating_currency" "EUR"

2020-01-01 open Assets:Broker
2020-01-01 open Equity:Opening

2020-01-01 * "fund the broker"
  Assets:Broker  100 USD
  Assets:Broker  100 EUR
  Assets:Broker  10 AAA {10 USD}
  Equity:Opening

2021-01-01 price AAA  12 USD
2021-01-01 price EUR   1.25 USD
"""


@pytest.mark.parametrize("currency", ["USD", "EUR"])
def test_cash_is_every_operating_currency_whatever_the_valuation_one(currency):
    entries, errors, options = loader.load_string(CASH_LEDGER)
    assert not errors, errors
    config = PortfolioConfig(
        name="test",
        accounts=["Assets:Broker"],
        commodity_targets={"AAA": Decimal("100")},
        class_targets={},
    )
    [report] = asset_allocation_report(
        entries,
        Pricer(prices.build_price_map(entries)),
        [config],
        currency,
        entries[-1].date,
        cash_currencies=options["operating_currency"],
    )
    commodity_report = report["commodityReport"]
    # neither cash currency is a holding, so AAA is the whole portfolio
    assert commodity_report["unconfigured"] == []
    assert [a["currentPct"] for a in commodity_report["assets"]] == [Decimal("100")]
    assert not commodity_report["diverged"]

import datetime
import unittest
from decimal import Decimal as D

from beancount.core.amount import Amount

from fava_portfolio_returns.api.investments import group_stats
from fava_portfolio_returns.test.test import approx2
from fava_portfolio_returns.test.test import load_portfolio_file


class TestInvestments(unittest.TestCase):
    def test_group_stats(self):
        p = load_portfolio_file("linear_growth_stock")
        stats = group_stats(p, datetime.date(2020, 1, 1), datetime.date(2020, 6, 1))
        assert stats == {
            "units": [
                Amount(D(2), "CORP"),
            ],
            "costValue": D("35"),
            "marketValue": D("70"),
            "totalPnl": D("35"),
            "realizedPnl": D("0"),
            "unrealizedPnl": D("35"),
            "irr": approx2(13.46),
            "mdm": approx2(1.71),
            "twr": 2.5,
        }

    def test_group_stats_partial_timeframe(self):
        p = load_portfolio_file("linear_growth_stock")
        stats = group_stats(p, datetime.date(2020, 1, 1), datetime.date(2020, 3, 1))
        assert stats == {
            "units": [
                Amount(D(1), "CORP"),
            ],
            "costValue": D("10"),
            "marketValue": D("20"),
            "totalPnl": D("10"),
            "realizedPnl": D("0"),
            "unrealizedPnl": D("10"),
            "irr": approx2(62.27),
            "mdm": approx2(0.98),
            "twr": 1.0,
        }

    def test_group_stats_target_currency(self):
        # in USD
        p = load_portfolio_file("target_currency", target_currency="USD")
        stats = group_stats(p, datetime.date(2020, 1, 1), datetime.date(2020, 12, 31))
        assert stats == {
            "units": [
                Amount(D(100), "CORP"),
            ],
            "costValue": D("100"),
            "marketValue": D("200"),
            "totalPnl": D("100"),
            "realizedPnl": D("0"),
            "unrealizedPnl": D("100"),
            "irr": approx2(1.12),
            "mdm": approx2(0.99),
            "twr": 1.0,
        }

        # converted to EUR
        p = load_portfolio_file("target_currency", target_currency="EUR")
        stats = group_stats(p, datetime.date(2020, 1, 1), datetime.date(2020, 12, 31))
        assert stats == {
            "units": [
                Amount(D(100), "CORP"),
            ],
            "costValue": D("50"),  # half of USD
            "marketValue": D("100"),  # half of USD
            "totalPnl": D("50"),  # half of USD
            "realizedPnl": D("0"),
            "unrealizedPnl": D("50"),  # half of USD
            "irr": approx2(1.12),
            "mdm": approx2(0.99),
            "twr": 1.0,
        }

    def test_group_stats_realized(self):
        p = load_portfolio_file("example_stock")
        stats = group_stats(p, datetime.date(2020, 1, 1), datetime.date(2020, 7, 10))
        assert stats == {
            "units": [
                Amount(D(250), "CORP"),
            ],
            "costValue": D("550"),
            "marketValue": D("750"),
            "totalPnl": D("230"),  # market value - cash
            "realizedPnl": D("30"),  # total P/L - unrealized P/L
            "unrealizedPnl": D("200"),  # market value - cost value
            "irr": approx2(2.12),
            "mdm": approx2(0.60),
            "twr": approx2(1.82),
        }

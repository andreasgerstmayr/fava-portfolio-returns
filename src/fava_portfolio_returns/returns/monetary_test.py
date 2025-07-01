import datetime
import unittest

from fava_portfolio_returns.core.intervals import intervals_heatmap
from fava_portfolio_returns.returns.monetary import MonetaryReturns
from fava_portfolio_returns.test.test import load_portfolio_file


class TestMonetaryReturns(unittest.TestCase):
    def test_heatmap_linear_growth_stock(self):
        p = load_portfolio_file("linear_growth_stock")
        intervals = intervals_heatmap(datetime.date(2020, 1, 1), datetime.date(2020, 12, 31))
        returns = MonetaryReturns().intervals(p, intervals)
        assert returns == [
            ("2020", 35.0),
            ("2020-01", 0.0),
            ("2020-02", 5.0),
            ("2020-03", 5.0),
            ("2020-04", 5.0),
            ("2020-05", 10.0),
            ("2020-06", 10.0),
            ("2020-07", 0.0),
            ("2020-08", 0.0),
            ("2020-09", 0.0),
            ("2020-10", 0.0),
            ("2020-11", 0.0),
            ("2020-12", 0.0),
        ]
        assert len(p.pricer.required_prices) == 12

    def test_heatmap_example_stock(self):
        p = load_portfolio_file("example_stock")
        intervals = intervals_heatmap(datetime.date(2020, 1, 1), datetime.date(2020, 12, 31))
        returns = MonetaryReturns().intervals(p, intervals)
        assert returns == [
            ("2020", 220.0),
            ("2020-01", 0.0),
            ("2020-02", -10.0),
            ("2020-03", 90.0),
            ("2020-04", 0.0),
            ("2020-05", -110.0),
            ("2020-06", -10.0),
            ("2020-07", 270.0),
            ("2020-08", -10.0),
            ("2020-09", 0.0),
            ("2020-10", 0.0),
            ("2020-11", 0.0),
            ("2020-12", 0.0),
        ]

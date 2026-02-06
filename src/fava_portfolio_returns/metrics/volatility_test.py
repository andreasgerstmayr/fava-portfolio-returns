import datetime
import unittest

from fava_portfolio_returns.metrics.volatility import Volatility
from fava_portfolio_returns.test.test import approx2
from fava_portfolio_returns.test.test import load_portfolio_file


class TestVolatility(unittest.TestCase):
    def test_single(self):
        p = load_portfolio_file("savings_plan")
        volatility = Volatility().single(p, datetime.date(2020, 1, 1), datetime.date(2020, 5, 1))
        assert volatility == approx2(0.72)

    def test_single_insufficient_data(self):
        p = load_portfolio_file("savings_plan")
        # Only one period return exists in this range -> volatility defaults to 0.
        volatility = Volatility().single(p, datetime.date(2020, 1, 1), datetime.date(2020, 2, 1))
        assert volatility == 0.0

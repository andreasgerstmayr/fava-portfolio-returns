import datetime
import unittest

from fava_portfolio_returns.returns.simple import SimpleReturns
from fava_portfolio_returns.test.test import approx2
from fava_portfolio_returns.test.test import load_portfolio_file


class TestSimple(unittest.TestCase):
    def test_series(self):
        p = load_portfolio_file("savings_plan")
        returns = SimpleReturns().series(p, datetime.date(2020, 1, 1), datetime.date(2020, 4, 1))
        assert returns == [
            (datetime.date(2020, 1, 1), 0.0),
            (datetime.date(2020, 2, 1), 0.2),
            (datetime.date(2020, 3, 1), approx2(0.33)),
            (datetime.date(2020, 4, 1), approx2(0.42)),
        ]

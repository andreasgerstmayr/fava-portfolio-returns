import datetime
import unittest
from pathlib import Path

from fava_portfolio_returns.core.intervals import intervals_yearly
from fava_portfolio_returns.returns.mdm import ModifiedDietzMethod
from fava_portfolio_returns.test.test import approx3
from fava_portfolio_returns.test.test import load_portfolio_file


class TestMDM(unittest.TestCase):
    def test_intervals(self):
        p = load_portfolio_file(Path("example/example.beancount"), investment_filter=["g:Gold"])
        intervals = intervals_yearly(datetime.date(2023, 1, 1))
        returns = ModifiedDietzMethod().intervals(p, intervals)
        # compare with values generated by beangrow
        assert returns == [
            ("2008", 0.0),
            ("2009", 0.0),
            ("2010", 0.0),
            ("2011", 0.0),
            ("2012", 0.0),
            ("2013", 0.0),
            ("2014", 0.0),
            ("2015", 0.0),
            ("2016", 0.0),
            ("2017", 0.0),
            ("2018", 0.0),
            ("2019", 0.0),
            ("2020", approx3(0.030)),
            ("2021", approx3(-0.066)),
            ("2022", approx3(0.072)),
            ("2023", 0.0),
        ]

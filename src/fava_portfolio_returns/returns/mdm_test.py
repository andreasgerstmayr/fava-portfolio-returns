import datetime
import unittest
from pathlib import Path

from beancount import loader

from fava_portfolio_returns.core.intervals import intervals_yearly
from fava_portfolio_returns.core.portfolio import Portfolio
from fava_portfolio_returns.returns.mdm import ModifiedDietzMethod


class TestMDM(unittest.TestCase):
    def test_intervals(self):
        entries, _errors, options = loader.load_file("example/example.beancount")
        p = Portfolio(entries, options, Path("example/beangrow.pbtxt"))
        intervals = intervals_yearly(datetime.date(2023, 1, 1))
        returns = ModifiedDietzMethod().intervals(p.pricer, p.filter_account_data_list("g:Gold"), "USD", intervals)
        # compare with values generated by beangrow
        assert [(date, f"{returns:.1%}") for date, returns in returns] == [
            ("2008", "0.0%"),
            ("2009", "0.0%"),
            ("2010", "0.0%"),
            ("2011", "0.0%"),
            ("2012", "0.0%"),
            ("2013", "0.0%"),
            ("2014", "0.0%"),
            ("2015", "0.0%"),
            ("2016", "0.0%"),
            ("2017", "0.0%"),
            ("2018", "0.0%"),
            ("2019", "0.0%"),
            ("2020", "4.2%"),
            ("2021", "-6.6%"),
            ("2022", "7.3%"),
            ("2023", "0.0%"),
        ]

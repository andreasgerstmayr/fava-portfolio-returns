import datetime
import unittest
from decimal import Decimal
from pathlib import Path

from beancount import loader

from fava_portfolio_returns.api.dividends import get_dividends
from fava_portfolio_returns.core.portfolio import Portfolio


class TestDividends(unittest.TestCase):
    def test_intervals(self):
        entries, _errors, options = loader.load_file("example/example.beancount")
        p = Portfolio(entries, options, Path("example/beangrow.pbtxt"))
        dividends = get_dividends(
            p.pricer,
            p.investment_groups,
            p.account_data_list,
            "USD",
            datetime.date(2020, 1, 1),
            datetime.date(2023, 1, 1),
            "monthly",
        )
        assert dividends == {
            "SPDR Gold Trust (ETF)": {
                "12/2021": Decimal("90.18"),
                "6/2021": Decimal("45.37"),
            },
            "Vanguard FTSE Developed Markets ETF": {
                "12/2020": Decimal("29.60"),
            },
            "Vanguard Health Care ETF": {
                "9/2021": Decimal("64.97"),
            },
            "iShares Core S&P Total U.S. Stock Market ETF": {
                "3/2021": Decimal("29.60"),
                "9/2020": Decimal("0.00"),
            },
        }

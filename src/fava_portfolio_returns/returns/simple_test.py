import datetime
import unittest
from decimal import Decimal

from beancount import loader

from fava_portfolio_returns.core.portfolio import Portfolio
from fava_portfolio_returns.returns.simple import SimpleReturns
from fava_portfolio_returns.test.test import BEANGROW_CONFIG_CORP

LEDGER = """
plugin "beancount.plugins.auto_accounts"
plugin "beancount.plugins.implicit_prices"

2020-01-01 commodity CORP
  name: "Example Stock"

2020-01-01 * "Buy 100 CORP @ 1 USD"
  Assets:Cash                           -100.00 USD
  Assets:CORP                               100 CORP {1 USD}

; 2020-01-01 cost 100 USD, market value 100 USD

2020-06-01 * "Buy 100 CORP @ 2 USD"
  Assets:Cash                           -200.00 USD
  Assets:CORP                               100 CORP {2 USD}

; 2020-06-01 cost 300 USD, market value 400 USD

2020-12-31 price CORP 3 USD

; 2020-12-31 cost 300 USD, market value 600 USD
"""


class TestSimple(unittest.TestCase):
    def test_series(self):
        entries, _errors, options = loader.load_string(LEDGER)
        p = Portfolio(entries, options, BEANGROW_CONFIG_CORP)
        returns = SimpleReturns().series(
            p.pricer, p.account_data_list, "USD", datetime.date(2020, 1, 1), datetime.date(2021, 1, 1)
        )
        assert returns == [
            (datetime.date(2020, 1, 1), Decimal(0)),
            (datetime.date(2020, 6, 1), (Decimal(400) - Decimal(300)) / Decimal(300)),
            (datetime.date(2020, 12, 31), Decimal(1)),
        ]

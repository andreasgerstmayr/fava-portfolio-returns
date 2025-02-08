import datetime
import unittest

from fava_portfolio_returns.returns.twr import TWR
from fava_portfolio_returns.test.test import BEANGROW_CONFIG_CORPAB
from fava_portfolio_returns.test.test import approx2
from fava_portfolio_returns.test.test import load_portfolio_file
from fava_portfolio_returns.test.test import load_portfolio_str


class TestTWR(unittest.TestCase):
    def test_series(self):
        p = load_portfolio_str(
            """
plugin "beancount.plugins.auto_accounts"
plugin "beancount.plugins.implicit_prices"

2020-01-01 commodity CORPA
2020-01-01 commodity CORPB

2020-01-01 *
  Assets:CORPA                               1 CORPA {100 USD}
  Assets:Cash

2020-07-01 *
  Assets:CORPB                               1 CORPB {200 USD}
  Assets:Cash

2020-07-01 price CORPA 105 USD

2020-12-01 *
  Assets:CORPA                               100/110 CORPA {110 USD}
  Assets:Cash

2020-12-01 *
  Assets:CORPB                               200/300 CORPB {300 USD}
  Assets:Cash
            """,
            BEANGROW_CONFIG_CORPAB,
        )
        returns = TWR().series(p, datetime.date(2020, 1, 1), datetime.date(2020, 12, 1))
        assert returns == [
            (datetime.date(2020, 1, 1), 0.0),
            (datetime.date(2020, 7, 1), approx2(0.05)),
            (datetime.date(2020, 12, 1), approx2(0.41)),
        ]

    def test_series_savings_plan(self):
        p = load_portfolio_file("savings_plan")
        returns = TWR().series(p, datetime.date(2020, 1, 1), datetime.date(2020, 4, 1))
        assert returns == [
            (datetime.date(2020, 1, 1), 0),
            (datetime.date(2020, 2, 1), 0.5),
            (datetime.date(2020, 3, 1), 1.0),
            (datetime.date(2020, 4, 1), 1.5),
        ]

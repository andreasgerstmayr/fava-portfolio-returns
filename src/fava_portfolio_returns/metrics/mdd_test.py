import datetime
import unittest

from fava_portfolio_returns.metrics.mdd import MDD
from fava_portfolio_returns.test.test import BEANGROW_CONFIG_CORP
from fava_portfolio_returns.test.test import approx3
from fava_portfolio_returns.test.test import load_portfolio_str


class TestMDD(unittest.TestCase):
    def test_single_drawdown(self):
        p = load_portfolio_str(
            """
plugin "beancount.plugins.auto_accounts"
plugin "beancount.plugins.implicit_prices"

2020-01-01 commodity CORP

2020-01-01 * "Buy 2 CORP @ 10 USD"
  Assets:Cash                          -20 USD
  Assets:CORP                            2 CORP {10 USD}

2020-01-02 price CORP 12 USD
2020-01-03 price CORP 5 USD
2020-01-04 price CORP 14 USD

2020-01-05 * "Sell 1 CORP @ 14 USD"
  Assets:Cash                         14 USD
  Assets:CORP                         -1 CORP {}
  Income:PnL

2020-01-06 price CORP 10 USD
2020-01-07 price CORP 1 USD

; date         price    peak   drawdown
; 2020-01-01   10.00   10.00      0.00%
; 2020-01-02   12.00   12.00      0.00%
; 2020-01-03    5.00   12.00     -0.58%
; 2020-01-04   14.00   14.00      0.00%
; 2020-01-05   14.00   14.00      0.00%
; 2020-01-06   10.00   14.00     -0.28%
; 2020-01-07    1.00   14.00     -0.92%
            """,
            BEANGROW_CONFIG_CORP,
        )

        start = datetime.date(2020, 1, 1)
        end = datetime.date(2020, 1, 7)

        # max drawdown
        assert MDD().single(p, start, end) == approx3(-0.928)

        # drawdown series
        series = MDD().series(p, start, end)
        assert series == [
            (datetime.date(2020, 1, 1), 0),
            (datetime.date(2020, 1, 2), 0),
            (datetime.date(2020, 1, 3), approx3(-0.583)),
            (datetime.date(2020, 1, 4), 0),
            (datetime.date(2020, 1, 5), 0),
            (datetime.date(2020, 1, 6), approx3(-0.285)),
            (datetime.date(2020, 1, 7), approx3(-0.928)),
        ]

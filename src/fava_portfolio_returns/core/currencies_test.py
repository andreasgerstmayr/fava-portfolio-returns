import datetime
import unittest

from fava_portfolio_returns.metrics.returns import Returns
from fava_portfolio_returns.test.test import BEANGROW_CONFIG_CORP
from fava_portfolio_returns.test.test import load_portfolio_str


class CurrenciesTest(unittest.TestCase):
    def test_indirect_currency_conversion(self):
        p = load_portfolio_str(
            """
plugin "beancount.plugins.auto_accounts"
plugin "beancount.plugins.implicit_prices"

2020-01-01 commodity CORP
  name: "Example Stock"

2020-01-01 commodity CURRENCY_BASE
2020-01-01 commodity CURRENCY_TARGET

2020-01-01 price CURRENCY_BASE  2 CURRENCY_TARGET

2020-01-01 * "Buy 50 CORP @ 2 CURRENCY_BASE"
  Assets:Cash                           -100.00 CURRENCY_BASE
  Assets:CORP                                50 CORP {2 CURRENCY_BASE}

2020-01-04 price CURRENCY_BASE 3 CURRENCY_TARGET

2020-02-01 price CORP  3 CURRENCY_BASE
2020-03-03 price CURRENCY_BASE  5 CURRENCY_TARGET
            """,
            BEANGROW_CONFIG_CORP,
        )

        p.target_currency = "CURRENCY_BASE"

        assert p.cash_at(datetime.date(2020, 1, 1)) == 100
        assert p.cash_at(datetime.date(2020, 1, 5)) == 100
        assert p.cash_at(datetime.date(2020, 2, 1)) == 100
        assert p.cash_at(datetime.date(2020, 3, 3)) == 100

        returns_base = Returns().series(p, datetime.date(2020, 1, 1), datetime.date(2020, 4, 1))
        assert returns_base == [
            (datetime.date(2020, 1, 1), 0.0),
            # investment has grown
            (datetime.date(2020, 2, 1), 0.5),
        ]

        p.target_currency = "CURRENCY_TARGET"

        # Cost basis of 100 CURRENCY_BASE = 200 CURRENCY_TARGET
        assert p.cash_at(datetime.date(2020, 1, 1)) == 200
        # Cost basis of 100 CURRENCY_BASE = 300 CURRENCY_TARGET
        assert p.cash_at(datetime.date(2020, 1, 5)) == 300
        # Cost basis of 100 CURRENCY_BASE = 300 CURRENCY_TARGET
        assert p.cash_at(datetime.date(2020, 2, 1)) == 300
        # Cost basis of 100 CURRENCY_BASE = 500 CURRENCY_TARGET
        assert p.cash_at(datetime.date(2020, 3, 3)) == 500

        returns_target = Returns().series(p, datetime.date(2020, 1, 1), datetime.date(2020, 4, 1))
        # Note more data points since the currency rates are now affecting how the portfolio evaluations are done
        assert returns_target == [
            # 200 CURRENCY_TARGET = 100 CURRENCY_BASE invested
            (datetime.date(2020, 1, 1), 0.0),
            # currency rate changing doesn't change the cost basis
            # (300 CURRENCY_TARGET invested)
            (datetime.date(2020, 1, 4), 0.0),
            # investment has acrually grown
            # (300 CURRENCY_TARGET invested, 50 CORP valued at 150 CURRENCY_BASE = 450 CURRENCY_TARGET)
            (datetime.date(2020, 2, 1), 0.5),
            # currency rate changing again doesn't change the cost basis (500 CURRENCY_TARGET invested)
            (datetime.date(2020, 3, 3), 0.5),
        ]

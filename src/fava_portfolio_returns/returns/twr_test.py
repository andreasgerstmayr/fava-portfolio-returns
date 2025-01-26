import datetime
import unittest
from decimal import Decimal

from beancount import loader

from fava_portfolio_returns.core.portfolio import Portfolio
from fava_portfolio_returns.returns.twr import TWR, Subperiod, _twr
from fava_portfolio_returns.test.test import BEANGROW_CONFIG_CORP


class TestTWR(unittest.TestCase):
    def test_series(self):
        entries, _errors, options = loader.load_string("""
plugin "beancount.plugins.auto_accounts"
plugin "beancount.plugins.implicit_prices"

2020-01-01 commodity CORP
  name: "Example Stock"

2020-01-01 * "Buy 100 CORP @ 1 USD"
  Assets:Cash                           -100.00 USD
  Assets:CORP                               100 CORP {1 USD}

; 2020-02-01 before purchase: spent 100 USD, market value 200 USD: 100% returns

2020-02-01 * "Buy 100 CORP @ 2 USD"
  Assets:Cash                           -200.00 USD
  Assets:CORP                               100 CORP {2 USD}

2021-01-01 price CORP 3 USD

; 2021-01-01: spent 300 USD, market value 600 USD: 200% returns
        """)
        p = Portfolio(entries, options, BEANGROW_CONFIG_CORP)
        returns = TWR().series(
            p.pricer, p.account_data_list, "USD", datetime.date(2020, 1, 1), datetime.date(2021, 1, 1)
        )
        assert returns == [(datetime.date(2020, 2, 1), Decimal(1)), (datetime.date(2021, 1, 1), Decimal(2))]

    def test_filtered(self):
        entries, _errors, options = loader.load_string("""
plugin "beancount.plugins.auto_accounts"
plugin "beancount.plugins.implicit_prices"

2020-01-01 commodity CORP
  name: "Example Stock"

2020-01-01 * "Buy 100 CORP @ 1 USD"
  Assets:Cash                           -100.00 USD
  Assets:CORP                               100 CORP {1 USD}

; 2020-02-01 before purchase: spent 100 USD, market value 200 USD: 100% returns
2020-02-01 * "Buy 100 CORP @ 2 USD"
  Assets:Cash                           -200.00 USD
  Assets:CORP                               100 CORP {2 USD}

2021-01-01 price CORP 3 USD

; 2021-01-01: spent 300 USD, market value 600 USD: 200% returns
        """)
        p = Portfolio(entries, options, BEANGROW_CONFIG_CORP)
        returns = TWR().series(
            p.pricer, p.account_data_list, "USD", datetime.date(2020, 1, 15), datetime.date(2021, 1, 1)
        )
        assert returns == [(datetime.date(2020, 2, 1), Decimal(1)), (datetime.date(2021, 1, 1), Decimal(2))]

    def test_series_with_fees(self):
        entries, _errors, options = loader.load_string("""
plugin "beancount.plugins.auto_accounts"
plugin "beancount.plugins.implicit_prices"

2020-01-01 commodity CORP
  name: "Example Stock"

2020-01-01 * "Buy 100 CORP @ 1 USD"
  Assets:Cash                           -110.00 USD
  Assets:CORP                               100 CORP {1 USD}
  Expenses:Financial:Fees

2020-02-01 * "Buy 100 CORP @ 2 USD"
  Assets:Cash                           -210.00 USD
  Assets:CORP                               100 CORP {2 USD}
  Expenses:Financial:Fees

2021-01-01 price CORP 3 USD

; spent 320 USD, market value 600 USD
; virtual sell on 2021-01-01

; timeline
; market values before/after cashflow: 0/100, 190/400, 600/0
; cashflows:                            110,    210,   -600
; subperiods: 100 to 190, 400 to 600
        """)
        p = Portfolio(entries, options, BEANGROW_CONFIG_CORP)
        returns = TWR().series(
            p.pricer, p.account_data_list, "USD", datetime.date(2020, 1, 1), datetime.date(2021, 1, 1)
        )
        assert returns == [(datetime.date(2020, 2, 1), Decimal("0.90")), (datetime.date(2021, 1, 1), Decimal("1.85"))]

    def test_twr(self):
        # example on https://canadianportfoliomanagerblog.com/how-to-calculate-your-time-weighted-rate-of-return-twrr/
        self.assertAlmostEqual(
            _twr(  # pylint: disable=protected-access
                [
                    Subperiod(datetime.date(2013, 12, 31), Decimal(250000), Decimal(250000)),
                    Subperiod(datetime.date(2014, 9, 15), Decimal(25000), Decimal(315621)),
                    Subperiod(datetime.date(2014, 12, 31), Decimal(0), Decimal(298082)),
                ]
            ),
            Decimal("0.0979"),
            places=4,
        )

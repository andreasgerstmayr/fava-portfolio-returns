import datetime
import unittest

from fava_portfolio_returns.returns.twr import TWR
from fava_portfolio_returns.test.test import BEANGROW_CONFIG_CORP_CASH_FLOWS
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

    def test_twr_with_changing_target_currency(self):
        portfolio_str = """
plugin "beancount.plugins.auto_accounts"
plugin "beancount.plugins.implicit_prices"

2020-01-01 commodity CORP
  name: "Example Stock"

2020-01-01 commodity CURRENCY_BASE
2020-01-01 commodity CURRENCY_TARGET

2020-01-01 price CURRENCY_BASE  2 CURRENCY_TARGET

2020-01-01 * "Buy 100 CORP @ 2 CURRENCY_BASE"
  Assets:Cash                                            -200.00 CURRENCY_BASE
  Assets:CORP:SingleCashFlow                                100 CORP {2 CURRENCY_BASE}

2020-01-01 * "Buy 50 CORP @ 2 CURRENCY_BASE"
  Assets:Cash                                            -100.00 CURRENCY_BASE
  Assets:CORP:MultipleCashFlows                                50 CORP {2 CURRENCY_BASE}

2020-01-04 price CURRENCY_BASE 3 CURRENCY_TARGET
2020-02-01 price CORP  3 CURRENCY_BASE

2020-01-04 price CURRENCY_BASE 4 CURRENCY_TARGET

2020-03-01 * "Buy 50 CORP @ 3 CURRENCY_BASE"
  Assets:Cash                                            -150.00 CURRENCY_BASE
  Assets:CORP:MultipleCashFlows                                50 CORP {3 CURRENCY_BASE}

2020-03-03 price CURRENCY_BASE 1.5 CURRENCY_TARGET

2020-03-15 price CORP  1.5 CURRENCY_BASE

2020-03-20 price CURRENCY_BASE  2 CURRENCY_TARGET
        """
        p_single = load_portfolio_str(
            portfolio_str,
            BEANGROW_CONFIG_CORP_CASH_FLOWS,
            investment_filter=["a_Assets:CORP:SingleCashFlow"],
        )
        p_multiple = load_portfolio_str(
            portfolio_str,
            BEANGROW_CONFIG_CORP_CASH_FLOWS,
            investment_filter=["a_Assets:CORP:MultipleCashFlows"],
        )

        p_single.target_currency = "CURRENCY_BASE"
        returns_single_base = TWR().series(p_single, datetime.date(2020, 1, 1), datetime.date(2020, 4, 1))
        assert returns_single_base == [
            (datetime.date(2020, 1, 1), 0.0),
            (datetime.date(2020, 2, 1), 0.5),
            (datetime.date(2020, 3, 1), 0.5),
            (datetime.date(2020, 3, 15), -0.25),
        ]

        p_single.target_currency = "CURRENCY_TARGET"
        returns_single_target = TWR().series(p_single, datetime.date(2020, 1, 1), datetime.date(2020, 4, 1))
        # Note more data points because the currency conversion dates are involved as well
        assert returns_single_target == [
            (datetime.date(2020, 1, 1), 0.0),
            (datetime.date(2020, 1, 4), 1.0),
            (datetime.date(2020, 2, 1), 2.0),
            (datetime.date(2020, 3, 1), 2.0),
            (datetime.date(2020, 3, 3), 0.125),
            (datetime.date(2020, 3, 15), -0.4375),
            # Note that as the conversion rate between currencies returns to original, the TWR becomes the same as with
            # CURRENCY_BASE
            (datetime.date(2020, 3, 20), -0.25),
        ]

        p_multiple.target_currency = "CURRENCY_BASE"
        returns_multiple_base = TWR().series(p_multiple, datetime.date(2020, 1, 1), datetime.date(2020, 4, 1))
        # results should be identical to p_single.target_currency = "CURRENCY_BASE" case because of the TWR definition
        assert returns_multiple_base == [
            (datetime.date(2020, 1, 1), 0.0),
            (datetime.date(2020, 2, 1), 0.5),
            (datetime.date(2020, 3, 1), 0.5),
            (datetime.date(2020, 3, 15), -0.25),
        ]

        p_multiple.target_currency = "CURRENCY_TARGET"
        returns_multiple_target = TWR().series(p_multiple, datetime.date(2020, 1, 1), datetime.date(2020, 4, 1))
        # results should be identical to p_single.target_currency = "CURRENCY_TARGET" case because of the TWR definition
        assert returns_multiple_target == [
            (datetime.date(2020, 1, 1), 0.0),
            (datetime.date(2020, 1, 4), 1.0),
            (datetime.date(2020, 2, 1), 2.0),
            (datetime.date(2020, 3, 1), 2.0),
            (datetime.date(2020, 3, 3), 0.125),
            (datetime.date(2020, 3, 15), -0.4375),
            # Note that as the conversion rate between currencies returns to original, the TWR becomes the same as with
            # CURRENCY_BASE
            (datetime.date(2020, 3, 20), -0.25),
        ]

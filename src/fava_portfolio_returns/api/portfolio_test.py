import datetime
import unittest
from decimal import Decimal

from beancount import loader

from fava_portfolio_returns.api.portfolio import portfolio_cost_values
from fava_portfolio_returns.core.portfolio import Portfolio
from fava_portfolio_returns.test.test import BEANGROW_CONFIG_CORP, BEANGROW_CONFIG_CORPAB


class TestPortfolio(unittest.TestCase):
    def test_cost_values(self):
        entries, _errors, options = loader.load_string("""
plugin "beancount.plugins.auto_accounts"
plugin "beancount.plugins.implicit_prices"

2020-01-01 commodity CORP
  name: "Example Stock"

2020-01-01 * "Buy 100 CORP @ 1 USD"
  Assets:Cash                           -100.00 USD
  Assets:CORP                               100 CORP {1 USD}

2020-02-01 * "Buy 100 CORP @ 2 USD"
  Assets:Cash                           -200.00 USD
  Assets:CORP                               100 CORP {2 USD}

2020-12-01 price CORP 3 USD
""")
        p = Portfolio(entries, options, BEANGROW_CONFIG_CORP)
        cost_values = portfolio_cost_values(
            p.pricer, p.account_data_list, "USD", datetime.date(2020, 1, 1), datetime.date(2021, 1, 1)
        )
        assert cost_values == [
            (datetime.date(2020, 1, 1), Decimal(100)),
            (datetime.date(2020, 2, 1), Decimal(300)),
        ]

    def test_cost_values_timefilter(self):
        entries, _errors, options = loader.load_string("""
plugin "beancount.plugins.auto_accounts"
plugin "beancount.plugins.implicit_prices"

2020-01-01 commodity CORP
  name: "Example Stock"

2020-01-01 * "Buy 100 CORP @ 1 USD"
  Assets:Cash                           -100.00 USD
  Assets:CORP                               100 CORP {1 USD}

2020-02-01 price CORP 1.5 USD

2020-06-01 * "Buy 100 CORP @ 2 USD"
  Assets:Cash                           -200.00 USD
  Assets:CORP                               100 CORP {2 USD}

2020-10-01 price CORP 3 USD

2020-11-01 * "Sell 200 CORP @ 3 USD"
  Assets:Cash                           600.00 USD
  Assets:CORP                               -200 CORP {}
""")
        p = Portfolio(entries, options, BEANGROW_CONFIG_CORP)
        cost_values = portfolio_cost_values(
            p.pricer, p.account_data_list, "USD", datetime.date(2020, 3, 1), datetime.date(2021, 1, 1)
        )
        assert cost_values == [
            (datetime.date(2020, 3, 1), Decimal(100)),
            (datetime.date(2020, 6, 1), Decimal(300)),
            (datetime.date(2020, 11, 1), Decimal(0)),
        ]

    def test_cost_values_multiple_commodities(self):
        entries, _errors, options = loader.load_string("""
plugin "beancount.plugins.auto_accounts"
plugin "beancount.plugins.implicit_prices"

2020-01-01 commodity CORPA
  name: "Example Stock"

2020-01-01 commodity CORPB
  name: "Example Stock"

2020-01-01 * "Buy 100 CORPA @ 1 USD"
  Assets:Cash                           -100.00 USD
  Assets:CORPA                              100 CORPA {1 USD}

2020-01-01 * "Buy 100 CORPB @ 1 USD"
  Assets:Cash                           -100.00 USD
  Assets:CORPB                              100 CORPB {1 USD}

2020-02-01 * "Buy 100 CORPA @ 2 USD"
  Assets:Cash                           -200.00 USD
  Assets:CORPA                              100 CORPA {2 USD}

2020-11-01 price CORPA 3 USD
""")
        p = Portfolio(entries, options, BEANGROW_CONFIG_CORPAB)
        cost_values = portfolio_cost_values(
            p.pricer, p.account_data_list, "USD", datetime.date(2020, 1, 1), datetime.date(2021, 1, 1)
        )
        assert cost_values == [
            (datetime.date(2020, 1, 1), Decimal(200)),
            (datetime.date(2020, 2, 1), Decimal(400)),
        ]

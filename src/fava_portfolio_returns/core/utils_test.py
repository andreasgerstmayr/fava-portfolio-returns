import datetime
import unittest

from fava_portfolio_returns.core.utils import market_value_of_inv
from fava_portfolio_returns.test.test import BEANGROW_CONFIG_CORP
from fava_portfolio_returns.test.test import load_portfolio_str


class TestUtils(unittest.TestCase):
    def test_get_market_value(self):
        p = load_portfolio_str(
            """
plugin "beancount.plugins.auto_accounts"
plugin "beancount.plugins.implicit_prices"

2020-01-01 commodity CORP
  name: "Example Stock"

2020-01-01 price EUR 2 USD

2020-01-01 * "Buy 100 CORP @ 1 USD"
  Assets:Cash                           -100.00 USD
  Assets:CORP                               100 CORP {1 USD}

2020-06-01 * "Buy 100 CORP @ 2 USD"
  Assets:Cash                           -200.00 USD
  Assets:CORP                               100 CORP {2 USD}

2020-11-01 price CORP 3 USD
            """,
            BEANGROW_CONFIG_CORP,
        )
        bal = p.account_data_list[0].balance
        assert market_value_of_inv(p.pricer, "USD", bal, datetime.date(2020, 1, 1)) == 200
        assert market_value_of_inv(p.pricer, "USD", bal, datetime.date(2020, 6, 1)) == 400
        assert market_value_of_inv(p.pricer, "USD", bal, datetime.date(2020, 11, 1)) == 600

        assert market_value_of_inv(p.pricer, "EUR", bal, datetime.date(2020, 1, 1)) == 100
        assert market_value_of_inv(p.pricer, "EUR", bal, datetime.date(2020, 6, 1)) == 200
        assert market_value_of_inv(p.pricer, "EUR", bal, datetime.date(2020, 11, 1)) == 300

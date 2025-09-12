import datetime
import unittest

from beancount.core.inventory import Inventory

from fava_portfolio_returns.core.portfolio import InvestmentAccount
from fava_portfolio_returns.core.portfolio import InvestmentGroup
from fava_portfolio_returns.core.portfolio import InvestmentsConfig
from fava_portfolio_returns.core.portfolio import LedgerCurrency
from fava_portfolio_returns.test.test import BEANGROW_CONFIG_CORP
from fava_portfolio_returns.test.test import load_portfolio_str


class TestPortfolio(unittest.TestCase):
    def test_read(self):
        p = load_portfolio_str(
            """
plugin "beancount.plugins.auto_accounts"
plugin "beancount.plugins.implicit_prices"

2020-01-01 commodity CORP
  name: "Example Stock"

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
        assert p.portfolio.investments_config == InvestmentsConfig(
            accounts=[InvestmentAccount(id="a:Assets:CORP", currency="CORP", assetAccount="Assets:CORP")],
            groups=[InvestmentGroup(id="g:CORP", name="CORP", investments=["Assets:CORP"], currency="")],
            currencies=[LedgerCurrency(id="c:CORP", currency="CORP", name="Example Stock", isInvestment=True)],
        )

    def test_balance_at(self):
        p = load_portfolio_str(
            """
plugin "beancount.plugins.auto_accounts"
plugin "beancount.plugins.implicit_prices"

2020-01-01 commodity CORP
  name: "Example Stock"

2020-01-01 * "Buy 100 CORP @ 1 USD"
  Assets:Cash                           -107.00 USD
  Assets:CORP                                50 CORP {2 USD}
  Expenses:Fees                            7.00 USD

2020-02-01 price CORP  3 USD
            """,
            BEANGROW_CONFIG_CORP,
        )
        assert p.balance_at(datetime.date(2020, 2, 1)) == Inventory.from_string("50 CORP {2 USD, 2020-01-01}")

    def test_cash_at(self):
        p = load_portfolio_str(
            """
plugin "beancount.plugins.auto_accounts"
plugin "beancount.plugins.implicit_prices"

2020-01-01 commodity CORP
  name: "Example Stock"

2020-01-01 * "Buy 100 CORP @ 1 USD"
  Assets:Cash                           -107.00 USD
  Assets:CORP                                50 CORP {2 USD}
  Expenses:Fees                            7.00 USD

2020-02-01 price CORP  3 USD
            """,
            BEANGROW_CONFIG_CORP,
        )
        assert p.cash_at(datetime.date(2020, 2, 1)) == 107

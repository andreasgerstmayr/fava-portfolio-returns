import datetime
import unittest

from beancount.core.inventory import Inventory

from fava_portfolio_returns.core.portfolio import InvestmentAccount
from fava_portfolio_returns.core.portfolio import InvestmentGroup
from fava_portfolio_returns.core.portfolio import InvestmentsConfig
from fava_portfolio_returns.core.portfolio import LedgerCurrency
from fava_portfolio_returns.test.test import BEANGROW_CONFIG_CORP
from fava_portfolio_returns.test.test import load_portfolio_str

LEDGER_CORP_WITH_PRICE = """
plugin "beancount.plugins.auto_accounts"
plugin "beancount.plugins.implicit_prices"

2020-01-01 commodity CORP
  name: "Example Stock"

2020-01-01 * "Buy 100 CORP @ 1 USD"
  Assets:Cash                           -100.00 USD
  Assets:CORP                               100 CORP {1 USD}

2020-11-01 price CORP 2 USD
"""


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
            accounts=[InvestmentAccount(id="a_Assets:CORP", currency="CORP", assetAccount="Assets:CORP")],
            groups=[InvestmentGroup(id="g_CORP", name="CORP", investments=["Assets:CORP"], currency="")],
            currencies=[LedgerCurrency(id="c_CORP", currency="CORP", name="Example Stock", isInvestment=True)],
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

    def test_get_missing_prices_none_actual_date(self):
        """get_missing_prices should not crash when beancount found no price at all (actual_date=None).

        This happens when a commodity has no price directives in the ledger, causing
        beancount's get_value to store (cost_currency, None, None) in required_prices.
        """
        p_filtered = load_portfolio_str(LEDGER_CORP_WITH_PRICE, BEANGROW_CONFIG_CORP)
        p = p_filtered.portfolio

        # Simulate a commodity where beancount found no price at all (actual_date=None).
        # This mirrors what beancount stores when prices.get_price() returns (None, None).
        required_date = datetime.date(2019, 6, 1)
        p.pricer.required_prices[("CORP", required_date)].add(("USD", None, None))

        # Should not raise TypeError: unsupported operand type(s) for -: 'datetime.date' and 'NoneType'
        missing_prices, _commands = p.get_missing_prices()

        none_date_entries = [mp for mp in missing_prices if mp["currency"] == "CORP" and mp["actualDate"] is None]
        assert len(none_date_entries) == 1
        assert none_date_entries[0]["requiredDate"] == required_date
        assert none_date_entries[0]["daysLate"] is None

    def test_get_missing_prices_future_date_none_actual_date(self):
        """get_missing_prices should skip entries with a future required_date even when actual_date=None."""
        p_filtered = load_portfolio_str(LEDGER_CORP_WITH_PRICE, BEANGROW_CONFIG_CORP)
        p = p_filtered.portfolio

        future_date = datetime.date.today() + datetime.timedelta(days=30)
        p.pricer.required_prices[("CORP", future_date)].add(("USD", None, None))

        missing_prices, _commands = p.get_missing_prices()

        future_entries = [mp for mp in missing_prices if mp["requiredDate"] == future_date]
        assert len(future_entries) == 0

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

import unittest

from beancount import loader

from fava_portfolio_returns.core.portfolio import (
    InvestmentAccount,
    InvestmentCurrency,
    InvestmentGroup,
    InvestmentGroups,
    Portfolio,
)
from fava_portfolio_returns.test.test import BEANGROW_CONFIG_CORP


class TestPortfolio(unittest.TestCase):
    def test_read(self):
        entries, _errors, options = loader.load_string("""
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
""")
        p = Portfolio(entries, options, BEANGROW_CONFIG_CORP)
        assert p.investment_groups == InvestmentGroups(
            accounts=[InvestmentAccount(id="a:Assets:CORP", currency="CORP", assetAccount="Assets:CORP")],
            groups=[InvestmentGroup(id="g:CORP", name="CORP", investments=["Assets:CORP"])],
            currencies=[InvestmentCurrency(id="c:CORP", currency="CORP", name="Example Stock")],
        )

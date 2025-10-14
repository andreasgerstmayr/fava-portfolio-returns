import datetime
import unittest
from decimal import Decimal as D
from beancount import loader
from beancount.core.amount import Amount
from beancount.core import getters
from beancount.core import prices
from pytest import approx
from fava_portfolio_returns._vendor.beangrow.config import read_config_from_string
from fava_portfolio_returns._vendor.beangrow.investments import extract, CashFlow
from fava_portfolio_returns._vendor.beangrow.returns import Pricer, compute_irr, truncate_cash_flows


def load(ledger: str, beangrow_cfg: str):
    entries, errors, options_map = loader.load_string(ledger)
    if errors:
        raise ValueError(errors)

    dcontext = options_map["dcontext"]
    accounts = getters.get_accounts(entries)
    price_map = prices.build_price_map(entries)
    pricer = Pricer(price_map)
    beangrow_config = read_config_from_string(beangrow_cfg, [], list(accounts))
    account_data_map = extract(entries, dcontext, beangrow_config, entries[-1].date, False, "")

    return pricer, account_data_map


TEST_CONFIG = """
investments {
  investment {
    currency: "CORP"
    asset_account: "Assets:CORP"
    dividend_accounts: "Income:CORP:Dividend"
    cash_accounts: "Assets:Cash"
  }
}
groups {
  group {
    name: "CORP"
    investment: "Assets:CORP"
  }
}
"""

TEST_LEDGER = """
plugin "beancount.plugins.auto_accounts"
plugin "beancount.plugins.implicit_prices"

2020-01-01 commodity CORP

2020-12-28 * "Buy 1 CORP"
  Assets:CORP                                           1 CORP {101 USD}
  Assets:Cash

2020-12-29 * "Buy 1 CORP"
  Assets:CORP                                           1 CORP {102 USD}
  Assets:Cash

2020-12-30 * "Buy 1 CORP"
  Assets:CORP                                           1 CORP {103 USD}
  Assets:Cash

2020-12-31 * "Buy 1 CORP"
  Assets:CORP                                           1 CORP {104 USD}
  Assets:Cash

2021-01-01 * "Buy 1 CORP"
  Assets:CORP                                           1 CORP {105 USD}
  Assets:Cash
"""


class ReturnsTest(unittest.TestCase):
    def test_truncate_cash_flows(self):
        pricer, account_data_map = load(TEST_LEDGER, TEST_CONFIG)
        account_data = account_data_map["Assets:CORP"]

        cash_flows = truncate_cash_flows(
            pricer, account_data, datetime.date(2020, 12, 30), datetime.date(2021, 1, 1)
        )
        assert cash_flows == [
            # truncate flows before 2020-12-30
            # balance before 2020-12-30: 2 CORP
            # price on 2020-12-30: 103 USD
            CashFlow(
                date=datetime.date(2020, 12, 30),
                amount=Amount(D(-2 * 103), "USD"),
                is_dividend=False,
                source="open",
                account="Assets:CORP",
                transaction=None,
            ),
            CashFlow(
                date=datetime.date(2020, 12, 30),
                amount=Amount(D(-103), "USD"),
                is_dividend=False,
                source="cash",
                account="Assets:CORP",
                transaction=account_data.transactions[2],
            ),
            CashFlow(
                date=datetime.date(2020, 12, 31),
                amount=Amount(D(-104), "USD"),
                is_dividend=False,
                source="cash",
                account="Assets:CORP",
                transaction=account_data.transactions[3],
            ),
            # balance before 2021-01-01: 4 CORP
            # price on 2020-12-31: 104 USD
            CashFlow(
                date=datetime.date(2021, 1, 1),
                amount=Amount(D(4 * 104), "USD"),
                is_dividend=False,
                source="close",
                account="Assets:CORP",
                transaction=None,
            ),
        ]

    def test_compute_irr(self):
        pricer, account_data_map = load(TEST_LEDGER, TEST_CONFIG)
        cash_flows = truncate_cash_flows(
            pricer, account_data_map["Assets:CORP"], datetime.date(2020, 12, 30), datetime.date(2021, 1, 1)
        )

        # 206 USD invested for 2 days + 103 USD invested for 2 days + 104 USD invested for 1 day = 416 USD
        # 206*(1+x)^(2/365) + 103*(1+x)^(2/365) + 104*(1+x)^(1/365) = 416
        irr = compute_irr(cash_flows, pricer, "USD", datetime.date(2021, 1, 1))
        assert irr == approx(3.530, abs=0.001)

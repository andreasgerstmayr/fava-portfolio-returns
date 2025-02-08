import datetime
import unittest
from decimal import Decimal as D
from pathlib import Path

from fava_portfolio_returns.api.portfolio import PortfolioValue
from fava_portfolio_returns.api.portfolio import portfolio_allocation
from fava_portfolio_returns.api.portfolio import portfolio_values
from fava_portfolio_returns.test.test import BEANGROW_CONFIG_CORP
from fava_portfolio_returns.test.test import BEANGROW_CONFIG_CORPAB
from fava_portfolio_returns.test.test import load_portfolio_file
from fava_portfolio_returns.test.test import load_portfolio_str


class TestPortfolio(unittest.TestCase):
    def test_allocation(self):
        p = load_portfolio_file(Path("example/example.beancount"))
        allocation = portfolio_allocation(p, datetime.date(2023, 1, 1))
        assert allocation == [
            {
                "name": "American Funds The Growth Fund of America Class R-6",
                "currency": "RGAGX",
                "marketValue": D("45877.18693"),
            },
            {
                "name": "Vanguard Total Bond Market Index Fund Institutional Plus Shares",
                "currency": "VBMPX",
                "marketValue": D("28014.42410"),
            },
            {
                "name": "SPDR Gold Trust (ETF)",
                "currency": "GLD",
                "marketValue": D("7517.64"),
            },
            {
                "name": "iShares Core S&P Total U.S. Stock Market ETF",
                "currency": "ITOT",
                "marketValue": D("4975.95"),
            },
            {
                "name": "Vanguard FTSE Developed Markets ETF",
                "currency": "VEA",
                "marketValue": D("4457.40"),
            },
            {
                "name": "Vanguard Health Care ETF",
                "currency": "VHT",
                "marketValue": D("3850.56"),
            },
        ]

    def test_portfolio_values_price_before_first_txn(self):
        p = load_portfolio_str(
            """
plugin "beancount.plugins.auto_accounts"
plugin "beancount.plugins.implicit_prices"

2020-01-01 commodity CORP
2020-01-01 price CORP                                  10 USD ; prices before first txn will be skipped

2020-02-01 * "Buy 1 CORP"
  Assets:Cash                                       -8.00 USD
  Assets:CORP                                           1 CORP {5 USD}
  Expenses:Fees
            """,
            BEANGROW_CONFIG_CORP,
        )
        chart = portfolio_values(p, datetime.date(2019, 1, 1), datetime.date(2020, 5, 1))
        assert chart == [
            PortfolioValue(date=datetime.date(2020, 2, 1), market=D(5), cost=D(5), cash=D(8)),
        ]

    def test_portfolio_values_start_date_before_first_txn(self):
        p = load_portfolio_str(
            """
plugin "beancount.plugins.auto_accounts"
plugin "beancount.plugins.implicit_prices"

2020-01-01 commodity CORP

2020-01-01 * "Buy 1 CORP"
  Assets:Cash                                       -8.00 USD
  Assets:CORP                                           1 CORP {5 USD}
  Expenses:Fees

2020-02-01 price CORP                                  10 USD
2020-03-01 price CORP                                  15 USD
2020-04-01 price CORP                                  20 USD

2020-05-01 * "Sell 1 CORP"
  Assets:Cash                                      -17.00 USD
  Assets:CORP                                          -1 CORP {}
  Expenses:Fees
            """,
            BEANGROW_CONFIG_CORP,
        )
        chart = portfolio_values(p, datetime.date(2019, 1, 1), datetime.date(2020, 5, 1))
        assert chart == [
            PortfolioValue(date=datetime.date(2020, 1, 1), market=D(5), cost=D(5), cash=D(8)),
            PortfolioValue(date=datetime.date(2020, 2, 1), market=D(10), cost=D(5), cash=D(8)),
            PortfolioValue(date=datetime.date(2020, 3, 1), market=D(15), cost=D(5), cash=D(8)),
            PortfolioValue(date=datetime.date(2020, 4, 1), market=D(20), cost=D(5), cash=D(8)),
            PortfolioValue(date=datetime.date(2020, 5, 1), market=D(0), cost=D(0), cash=D(25)),
        ]

    def test_portfolio_values_start_date_exact(self):
        p = load_portfolio_str(
            """
plugin "beancount.plugins.auto_accounts"
plugin "beancount.plugins.implicit_prices"

2020-01-01 commodity CORP

2020-01-01 * "Buy 1 CORP"
  Assets:Cash                                       -8.00 USD
  Assets:CORP                                           1 CORP {5 USD}
  Expenses:Fees

2020-02-01 price CORP                                  10 USD
2020-03-01 price CORP                                  15 USD
2020-04-01 price CORP                                  20 USD

2020-05-01 * "Sell 1 CORP"
  Assets:Cash                                       17.00 USD
  Assets:CORP                                          -1 CORP {}
  Expenses:Fees
            """,
            BEANGROW_CONFIG_CORP,
        )
        chart = portfolio_values(p, datetime.date(2020, 2, 1), datetime.date(2020, 5, 1))
        assert chart == [
            PortfolioValue(date=datetime.date(2020, 2, 1), market=D(10), cost=D(5), cash=D(8)),
            PortfolioValue(date=datetime.date(2020, 3, 1), market=D(15), cost=D(5), cash=D(8)),
            PortfolioValue(date=datetime.date(2020, 4, 1), market=D(20), cost=D(5), cash=D(8)),
            PortfolioValue(date=datetime.date(2020, 5, 1), market=D(0), cost=D(0), cash=D(-9)),
        ]

    def test_portfolio_values_start_date_exact_last_entry(self):
        p = load_portfolio_str(
            """
plugin "beancount.plugins.auto_accounts"
plugin "beancount.plugins.implicit_prices"

2020-01-01 commodity CORP

2020-01-01 * "Buy 1 CORP"
  Assets:Cash                                       -8.00 USD
  Assets:CORP                                           1 CORP {5 USD}
  Expenses:Fees

2020-02-01 price CORP                                  10 USD
            """,
            BEANGROW_CONFIG_CORP,
        )
        chart = portfolio_values(p, datetime.date(2020, 2, 1), datetime.date(2020, 2, 29))
        assert chart == [
            PortfolioValue(date=datetime.date(2020, 2, 1), market=D(10), cost=D(5), cash=D(8)),
        ]

    def test_portfolio_values_truncate_start(self):
        p = load_portfolio_str(
            """
plugin "beancount.plugins.auto_accounts"
plugin "beancount.plugins.implicit_prices"

2020-01-01 commodity CORP

2020-01-01 * "Buy 1 CORP"
  Assets:Cash                                       -8.00 USD
  Assets:CORP                                           1 CORP {5 USD}
  Expenses:Fees

2020-02-01 price CORP                                  10 USD
; truncated entry will be here
2020-03-01 price CORP                                  15 USD
2020-04-01 price CORP                                  20 USD

2020-05-01 * "Sell 1 CORP"
  Assets:Cash                                      -17.00 USD
  Assets:CORP                                          -1 CORP {}
  Expenses:Fees
            """,
            BEANGROW_CONFIG_CORP,
        )
        chart = portfolio_values(p, datetime.date(2020, 2, 15), datetime.date(2020, 5, 1))
        assert chart == [
            PortfolioValue(date=datetime.date(2020, 2, 15), market=D(10), cost=D(5), cash=D(8)),  # truncated
            PortfolioValue(date=datetime.date(2020, 3, 1), market=D(15), cost=D(5), cash=D(8)),
            PortfolioValue(date=datetime.date(2020, 4, 1), market=D(20), cost=D(5), cash=D(8)),
            PortfolioValue(date=datetime.date(2020, 5, 1), market=D(0), cost=D(0), cash=D(25)),
        ]

    def test_portfolio_values_multiple_commodities(self):
        p = load_portfolio_str(
            """
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
            """,
            BEANGROW_CONFIG_CORPAB,
        )
        cost_values = portfolio_values(p, datetime.date(2020, 1, 1), datetime.date(2021, 1, 1))
        assert cost_values == [
            PortfolioValue(date=datetime.date(2020, 1, 1), market=D(200), cost=D(200), cash=D(200)),
            PortfolioValue(date=datetime.date(2020, 2, 1), market=D(500), cost=D(400), cash=D(400)),
            PortfolioValue(date=datetime.date(2020, 11, 1), market=D(700), cost=D(400), cash=D(400)),
        ]

import datetime
import unittest
from decimal import Decimal as D
from pathlib import Path

from beancount.core.amount import Amount

from fava_portfolio_returns.api.cash_flows import CashFlowChartValue
from fava_portfolio_returns.api.cash_flows import cash_flows_chart
from fava_portfolio_returns.api.cash_flows import cash_flows_table
from fava_portfolio_returns.api.cash_flows import dividends_chart
from fava_portfolio_returns.test.test import load_portfolio_file


class TestCashFlows(unittest.TestCase):
    def test_cash_flows_chart(self):
        p = load_portfolio_file("linear_growth_stock")
        chart = cash_flows_chart(p, datetime.date(2020, 1, 1), datetime.date(2020, 6, 1), "monthly")
        assert chart == [
            CashFlowChartValue(date="2020-01", div=D(0), exdiv=D(-10)),
            CashFlowChartValue(date="2020-04", div=D(0), exdiv=D(-25)),
        ]

    def test_cash_flows_table(self):
        p = load_portfolio_file("linear_growth_stock")
        table = cash_flows_table(p, datetime.date(2020, 1, 1), datetime.date(2020, 6, 1))
        assert table == [
            {
                "date": datetime.date(2020, 4, 1),
                "amount": Amount(D(-25), "USD"),
                "isDividend": False,
                "source": "cash",
                "account": "Assets:CORP",
                "transaction": "Buy 1 CORP",
            },
            {
                "date": datetime.date(2020, 1, 1),
                "amount": Amount(D(-10), "USD"),
                "isDividend": False,
                "source": "cash",
                "account": "Assets:CORP",
                "transaction": "Buy 1 CORP",
            },
        ]

    def test_dividends(self):
        p = load_portfolio_file(Path("example/example.beancount"))
        chart = dividends_chart(p, datetime.date(2020, 1, 1), datetime.date(2023, 1, 1), "monthly")
        assert chart == [
            {
                "date": "2020-09",
                "iShares Core S&P Total U.S. Stock Market ETF": D("0.00"),
            },
            {
                "date": "2020-12",
                "Vanguard FTSE Developed Markets ETF": D("29.60"),
            },
            {
                "date": "2021-03",
                "iShares Core S&P Total U.S. Stock Market ETF": D("29.60"),
            },
            {
                "date": "2021-06",
                "SPDR Gold Trust (ETF)": D("45.37"),
            },
            {
                "date": "2021-09",
                "Vanguard Health Care ETF": D("64.97"),
            },
            {
                "date": "2021-12",
                "SPDR Gold Trust (ETF)": D("90.18"),
            },
        ]

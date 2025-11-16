import datetime
import unittest
from decimal import Decimal as D

from beancount import Amount
from beancount import Position

from fava_portfolio_returns.core.pricer import CurrencyConversionException
from fava_portfolio_returns.test.test import BEANGROW_CONFIG_CORP
from fava_portfolio_returns.test.test import load_portfolio_str

oneUSD = Amount(D(1), "USD")
halfEUR = Amount(D(0.5), "EUR")


class TestPricer(unittest.TestCase):
    def test_convert_amt(self):
        p = load_portfolio_str(
            """
2020-01-02 price EUR 2 USD
            """,
            BEANGROW_CONFIG_CORP,
        )

        with self.assertRaises(CurrencyConversionException) as ctx:
            p.pricer.convert_amount(oneUSD, "EUR", datetime.date(2020, 1, 1))
        assert (
            ctx.exception.message
            == "Could not convert USD to EUR on 2020-01-01. Please add a price directive '2020-01-01 price USD <conversion_rate> EUR' to your ledger."
        )
        assert p.pricer.convert_amount(oneUSD, "EUR", datetime.date(2020, 1, 2)) == halfEUR
        assert p.pricer.convert_amount(oneUSD, "EUR", datetime.date(2020, 1, 3)) == halfEUR

    def test_convert_post(self):
        p = load_portfolio_str(
            """
2020-01-02 price EUR 2 USD
            """,
            BEANGROW_CONFIG_CORP,
        )

        with self.assertRaises(CurrencyConversionException) as ctx:
            p.pricer.convert_position(Position(units=oneUSD), "EUR", datetime.date(2020, 1, 1))
        assert (
            ctx.exception.message
            == "Could not convert USD to EUR on 2020-01-01. Please add a price directive '2020-01-01 price USD <conversion_rate> EUR' to your ledger."
        )
        assert p.pricer.convert_position(Position(units=oneUSD), "EUR", datetime.date(2020, 1, 2)) == halfEUR
        assert p.pricer.convert_position(Position(units=oneUSD), "EUR", datetime.date(2020, 1, 3)) == halfEUR

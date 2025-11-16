import datetime
from typing import Optional

from beancount import Amount
from beancount import Currency
from beancount import Position
from beancount.core import convert
from fava.helpers import FavaAPIError

from fava_portfolio_returns._vendor.beangrow.returns import Pricer as BeangrowPricer


class CurrencyConversionException(FavaAPIError):
    def __init__(self, source: str, target: str, date: Optional[datetime.date] = None):
        date = date or datetime.date.today()
        super().__init__(
            f"Could not convert {source} to {target} on {date}."
            f" Please add a price directive '{date} price {source} <conversion_rate> {target}' to your ledger."
        )


class Pricer(BeangrowPricer):
    def convert_amount(self, amount: Amount, target_currency: Currency, date: datetime.date) -> Amount:
        # convert_amount silently returns the original amount if conversion is not possible; throw an exception instead
        target_amt = super().convert_amount(amount, target_currency, date)
        if target_amt.currency != target_currency:
            raise CurrencyConversionException(target_amt.currency, target_currency, date)
        return target_amt

    def convert_position(self, pos: Position, target_currency: Currency, date: Optional[datetime.date] = None):
        target_pos = convert.convert_position(pos, target_currency, self.price_map, date)
        if target_pos.currency != target_currency:
            raise CurrencyConversionException(target_pos.currency, target_currency, date)
        return target_pos

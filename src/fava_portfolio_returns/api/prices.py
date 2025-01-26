from beancount.core import prices
from beangrow.returns import Pricer


def get_prices(pricer: Pricer, target_currency: str, currency: str):
    return prices.get_all_prices(pricer.price_map, (currency, target_currency))

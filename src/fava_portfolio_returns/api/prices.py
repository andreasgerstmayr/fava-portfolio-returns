import beangrow.returns as returnslib
from beancount.core import prices


def get_prices(pricer: returnslib.Pricer, target_currency: str, currency: str):
    return prices.get_all_prices(pricer.price_map, (currency, target_currency))

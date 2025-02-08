from fava_portfolio_returns.returns.base import ReturnsBase
from fava_portfolio_returns.returns.irr import IRR
from fava_portfolio_returns.returns.mdm import ModifiedDietzMethod
from fava_portfolio_returns.returns.monetary import MonetaryReturns
from fava_portfolio_returns.returns.simple import SimpleReturns
from fava_portfolio_returns.returns.twr import TWR

RETURN_METHODS: dict[str, ReturnsBase] = {
    "simple": SimpleReturns(),
    "irr": IRR(),
    "mdm": ModifiedDietzMethod(),
    "twr": TWR(),
    "monetary": MonetaryReturns(),
}

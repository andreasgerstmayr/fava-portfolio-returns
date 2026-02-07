from fava_portfolio_returns.metrics.base import MetricBase
from fava_portfolio_returns.metrics.irr import IRR
from fava_portfolio_returns.metrics.mdd import MDD
from fava_portfolio_returns.metrics.mdm import ModifiedDietzMethod
from fava_portfolio_returns.metrics.pnl import TotalPNL
from fava_portfolio_returns.metrics.returns import Returns
from fava_portfolio_returns.metrics.twr import TWR
from fava_portfolio_returns.metrics.volatility import Volatility


def get_metric(name: str):
    metric = _registry.get(name)
    if not metric:
        raise ValueError(f"Invalid metric '{name}'")
    return metric


_registry: dict[str, MetricBase] = {
    "returns": Returns(),
    "irr": IRR(),
    "mdm": ModifiedDietzMethod(),
    "twr": TWR(),
    "pnl": TotalPNL(),
    "volatility": Volatility(),
    "mdd": MDD(),
}

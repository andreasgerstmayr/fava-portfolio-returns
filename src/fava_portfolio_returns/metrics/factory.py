from fava_portfolio_returns.metrics.base import MetricBase
from fava_portfolio_returns.metrics.irr import IRR
from fava_portfolio_returns.metrics.mdm import ModifiedDietzMethod
from fava_portfolio_returns.metrics.pnl import TotalPNL
from fava_portfolio_returns.metrics.returns import Returns
from fava_portfolio_returns.metrics.twr import TWR

METRICS: dict[str, MetricBase] = {
    "returns": Returns(),
    "irr": IRR(),
    "mdm": ModifiedDietzMethod(),
    "twr": TWR(),
    "pnl": TotalPNL(),
}

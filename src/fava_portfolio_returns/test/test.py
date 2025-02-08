import ast
from pathlib import Path

from beancount import loader
from beancount.core.data import Custom
from pytest import approx

from fava_portfolio_returns.core.portfolio import FilteredPortfolio
from fava_portfolio_returns.core.portfolio import Portfolio

BEANGROW_CONFIG_CORP = """
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

BEANGROW_CONFIG_CORPAB = """
investments {
  investment {
    currency: "CORPA"
    asset_account: "Assets:CORPA"
    dividend_accounts: "Income:CORPA:Dividend"
    cash_accounts: "Assets:Cash"
  }
  investment {
    currency: "CORPB"
    asset_account: "Assets:CORPB"
    dividend_accounts: "Income:CORPB:Dividend"
    cash_accounts: "Assets:Cash"
  }
}
groups {
  group {
    name: "CORP"
    investment: "Assets:CORP*"
  }
}
"""


def load_portfolio_str(beancount: str, beangrow: str, target_currency="USD") -> FilteredPortfolio:
    entries, errors, options_map = loader.load_string(beancount)
    if errors:
        raise ValueError(errors)

    p = Portfolio(entries, options_map, beangrow)
    return p.filter([], target_currency)


def load_portfolio_file(ledger_path: str | Path, target_currency="USD", investment_filter=[]) -> FilteredPortfolio:
    if isinstance(ledger_path, str):
        ledger_path = Path(__file__).parent / "ledger" / f"{ledger_path}.beancount"
    entries, errors, options_map = loader.load_file(ledger_path)
    if errors:
        raise ValueError(errors)

    beangrow_config = "beangrow.pbtxt"
    for entry in entries:
        if isinstance(entry, Custom) and entry.type == "fava-extension" and len(entry.values) == 2:
            key, val = entry.values
            if key.value == "fava_portfolio_returns":
                cfg = ast.literal_eval(val.value)
                beangrow_config = cfg.get("beangrow_config", "beangrow.pbtxt")
                break

    p = Portfolio(entries, options_map, ledger_path.parent.joinpath(beangrow_config))
    return p.filter(investment_filter, target_currency)


def approx1(x):
    return approx(x, abs=0.1)


def approx2(x):
    return approx(x, abs=0.01)


def approx3(x):
    return approx(x, abs=0.001)

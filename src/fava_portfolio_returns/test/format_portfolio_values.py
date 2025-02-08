import argparse
import datetime
from pathlib import Path

from beancount.core.number import ZERO

from fava_portfolio_returns.api.portfolio import PortfolioValue
from fava_portfolio_returns.api.portfolio import portfolio_values
from fava_portfolio_returns.test.test import load_portfolio_file


def format_portfolio_values(values: list[PortfolioValue]):
    def returns(v: PortfolioValue):
        if v.cash == ZERO:
            return 0
        return v.market / v.cash - 1

    print(f"; {'date':<10}  {'market':>7}  {'cost':>7}  {'cash':>7}  {'gains':>7}  {'returns':>8}")
    for v in values:
        print(f"; {v.date}  {v.market:7.2f}  {v.cost:7.2f}  {v.cash:7.2f}  {v.market - v.cash:7.2f}  {returns(v):8.2%}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("ledger", type=Path)
    args = parser.parse_args()

    p = load_portfolio_file(args.ledger)
    values = portfolio_values(p, datetime.date(2000, 1, 1), datetime.date(3000, 1, 1))
    format_portfolio_values(values)


if __name__ == "__main__":
    main()

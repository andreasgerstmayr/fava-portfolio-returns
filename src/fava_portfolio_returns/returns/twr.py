import datetime
import logging
from collections import defaultdict
from decimal import Decimal
from typing import NamedTuple

import beangrow.returns as returnslib
from beancount.core.number import ZERO
from beangrow.investments import AccountData

from fava_portfolio_returns.core.utils import (
    compute_balance_at,
    convert_cash_flows_to_currency,
    get_market_value_of_inventory,
)
from fava_portfolio_returns.returns.base import ReturnsBase

logger = logging.getLogger(__name__)


class TWR(ReturnsBase):
    """Time-Weighted Rate of Return"""

    def single(
        self,
        pricer: returnslib.Pricer,
        account_data_list: list[AccountData],
        target_currency: str,
        start_date: datetime.date,
        end_date: datetime.date,
    ):
        subperiods = _get_subperiods(pricer, account_data_list, target_currency, start_date, end_date)
        return _twr(subperiods)

    def series(
        self,
        pricer: returnslib.Pricer,
        account_data_list: list[AccountData],
        target_currency: str,
        start_date: datetime.date,
        end_date: datetime.date,
    ):
        subperiods = _get_subperiods(pricer, account_data_list, target_currency, start_date, end_date)
        return _twr(subperiods, save_intermediate=True)


class Subperiod(NamedTuple):
    date: datetime.date
    cash_flows: Decimal
    # market value after cash flow
    market_value: Decimal


def _get_subperiods(
    pricer: returnslib.Pricer,
    account_data_list: list[AccountData],
    target_currency: str,
    start_date: datetime.date,
    end_date: datetime.date,
):
    cash_flows = returnslib.truncate_and_merge_cash_flows(pricer, account_data_list, start_date, end_date)
    cash_flows = convert_cash_flows_to_currency(pricer, target_currency, cash_flows)
    market_values: dict[datetime.date, Decimal] = {}

    # combine flows on same date
    flows_by_date: dict[datetime.date, Decimal] = defaultdict(Decimal)
    for flow in cash_flows:
        flows_by_date[flow.date] -= flow.amount.number

        # on close (i.e. the investment gets liquidated), the position will be empty
        # and therefore the market value should be 0.
        if flow.source == "close":
            market_values[flow.date] = ZERO

    subperiods = []
    for date, cost_value in sorted(flows_by_date.items(), key=lambda x: x[0]):
        if cost_value == ZERO:
            continue

        if date not in market_values:
            balance = compute_balance_at(account_data_list, date)
            market_values[date] = get_market_value_of_inventory(pricer, target_currency, balance, date)

        subperiods.append(Subperiod(date, cost_value, market_values[date]))
    return subperiods


def _twr(subperiods: list[Subperiod], save_intermediate=False):
    if logger.isEnabledFor(logging.DEBUG):
        logger.debug("Calculating TWR over subperiods")
        for i, subperiod in enumerate(subperiods):
            logger.debug(
                "Subperiod %d date=%s cash_flows=%.2f market_value=%.2f",
                i,
                subperiod.date,
                subperiod.cash_flows,
                subperiod.market_value,
            )

    twr = Decimal(1)
    twrs = []
    for i in range(1, len(subperiods)):
        # https://en.wikipedia.org/wiki/Time-weighted_return#Time-weighted_return_compensating_for_external_flows
        # portfolio is valued immediately after each external flow
        begin = subperiods[i - 1].market_value  # last period after cash flow
        if begin == 0:
            continue
        end = subperiods[i].market_value - subperiods[i].cash_flows  # current period before cash flow
        returns = end / begin
        twr *= returns

        if save_intermediate:
            twrs.append((subperiods[i].date, twr - 1))

        logger.debug(
            "Subperiod %d from %s-%s: begin=%.2f end=%.2f returns=%.2f%%",
            i,
            subperiods[i - 1].date,
            subperiods[i].date,
            begin,
            end,
            returns - 1,
        )

    return twrs if save_intermediate else (twr - 1)

# source: https://github.com/beancount/beangrow/blob/master/beangrow/returns.py
__copyright__ = "Copyright (C) 2020  Martin Blais"
__license__ = "GNU GPLv2"

import datetime
from typing import List
from typing import Optional

from beangrow.investments import AccountData
from beangrow.investments import CashFlow
from beangrow.investments import compute_balance_at
from beangrow.returns import Pricer

Date = datetime.date
ONE_DAY = datetime.timedelta(days=1)


# includes https://github.com/beancount/beangrow/pull/41
# TODO: remove once beangrow 1.0.2 is released
def truncate_cash_flows(  # noqa: C901
    pricer: Pricer,
    account_data: AccountData,
    date_start: Optional[Date],
    date_end: Optional[Date],
) -> List[CashFlow]:
    """Truncate the cash flows for the given account data."""

    start_flows = []
    end_flows = []

    if date_start is not None:
        # Truncate before the start date.
        balance = compute_balance_at(account_data.transactions, date_start)
        if not balance.is_empty():
            cost_balance = balance.reduce(pricer.get_value, date_start)
            cost_position = cost_balance.get_only_position()
            if cost_position:
                start_flows.append(
                    CashFlow(
                        date_start,
                        -cost_position.units,
                        False,  # noqa: FBT003
                        "open",
                        account_data.account,
                    )
                )

    if date_end is not None:
        # Truncate after the end date.
        # Note: Avoid redundant balance iteration by computing it once and
        # caching it on every single transaction.
        balance = compute_balance_at(account_data.transactions, date_end)
        if not balance.is_empty():
            cost_balance = balance.reduce(pricer.get_value, date_end - ONE_DAY)
            cost_position = cost_balance.get_only_position()
            if cost_position:
                end_flows.append(
                    CashFlow(
                        date_end,
                        cost_position.units,
                        False,  # noqa: FBT003
                        "close",
                        account_data.account,
                    )
                )

    # Compute truncated flows.
    truncated_flows = []
    for flow in account_data.cash_flows:
        if date_start and flow.date < date_start:
            continue
        if date_end and flow.date >= date_end:
            break
        truncated_flows.append(flow)

    cash_flows = start_flows + truncated_flows + end_flows

    cash_flows_dates = [cf.date for cf in cash_flows]

    if cash_flows_dates != sorted(cash_flows_dates):
        msg = "Cash flows are not sorted by date."
        raise ValueError(msg)

    return cash_flows


def truncate_and_merge_cash_flows(
    pricer: Pricer,
    account_data_list: List[AccountData],
    date_start: Optional[Date],
    date_end: Optional[Date],
) -> List[CashFlow]:
    """Truncate and merge the cash flows for given list of account data."""
    cash_flows = []
    for ad in account_data_list:
        cash_flows.extend(truncate_cash_flows(pricer, ad, date_start, date_end))
    cash_flows.sort(key=lambda item: item[0])
    return cash_flows

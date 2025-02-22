# monkey patching of unreleased beangrow features
# mypy: ignore-errors

import datetime
import typing
from typing import List
from typing import Optional

import beangrow.investments
import beangrow.returns
from beancount.core import convert
from beancount.core import data
from beancount.core.amount import Amount
from beangrow.investments import AccountData
from beangrow.investments import Cat
from beangrow.investments import compute_balance_at

# Basic type aliases.
Account = str
Date = datetime.date

ONE_DAY = datetime.timedelta(days=1)

# https://github.com/beancount/beangrow/pull/42
CashFlow = typing.NamedTuple(
    "CashFlow",
    [
        ("date", Date),
        ("amount", Amount),  # The amount of the cashflow.
        ("is_dividend", bool),  # True if the flow is a dividend.
        ("source", str),  # Source of this cash flow.
        ("account", Account),  # Asset account for which this was generated.
        ("transaction", Optional[data.Transaction]),  # Source transaction of this cash flow.
    ],
)
beangrow.investments.CashFlow = CashFlow


def produce_cash_flows_general(entry: data.Directive, account: Account) -> List[CashFlow]:
    """Produce cash flows using a generalized rule."""
    has_dividend = any(posting.meta["category"] == Cat.DIVIDEND for posting in entry.postings)
    flows = []
    for posting in entry.postings:
        category = posting.meta["category"]
        if category == Cat.CASH:
            assert not posting.cost
            cf = CashFlow(entry.date, convert.get_weight(posting), has_dividend, "cash", account, entry)
            posting.meta["flow"] = cf
            flows.append(cf)

        elif category == Cat.OTHERASSET:
            # If the account deposits other assets, count this as an outflow.
            cf = CashFlow(entry.date, convert.get_weight(posting), False, "other", account, entry)
            posting.meta["flow"] = cf
            flows.append(cf)

    return flows


beangrow.investments.produce_cash_flows_general = produce_cash_flows_general


# https://github.com/beancount/beangrow/pull/41
def truncate_cash_flows(  # noqa: C901
    pricer: beangrow.returns.Pricer,
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
                        None,
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
                        None,
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


beangrow.returns.truncate_cash_flows = truncate_cash_flows

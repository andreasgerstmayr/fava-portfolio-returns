#!/usr/bin/env python3
"""Library code to compute returns from series of cash flows."""

__copyright__ = "Copyright (C) 2020  Martin Blais"
__license__ = "GNU GPLv2"

import collections
import datetime
import itertools
import logging
import typing
from typing import List, Optional, Tuple

import numpy as np
from beancount.core import convert, data, prices
from beancount.core.amount import Amount
from beancount.core.inventory import Inventory
from beancount.core.number import ZERO
from beancount.core.position import Position
from scipy.optimize import fsolve

from fava_portfolio_returns._vendor.beangrow.investments import AccountData, CashFlow, Cat, compute_balance_at

# Basic type aliases.
Account = str
Currency = str
Date = datetime.date
Array = np.ndarray

ONE_DAY = datetime.timedelta(days=1)

class Pricer:
    """A price database that remembers the queried prices and dates."""

    def __init__(self, price_map: prices.PriceMap) -> None:
        """Create a new pricer object."""
        self.price_map = price_map
        self.required_prices = collections.defaultdict(set)

    def get_value(self, pos: Position, date: Date) -> Amount:
        """Return the value and save the conversion rate."""
        price_dates = []
        price = convert.get_value(pos, self.price_map, date, price_dates)

        # Add prices found to the list of queried ones.
        for found_date, found_rate in price_dates:
            self.required_prices[(pos.units.currency, date)].add(
                (price.currency, found_date, found_rate)
            )

        return price

    def convert_amount(
        self, amount: Amount, target_currency: Currency, date: Date
    ) -> Amount:
        """Convert an amount to a specific currency."""
        # TODO(blais): Save the amount here too.
        return convert.convert_amount(
            amount, target_currency, self.price_map, date=date
        )


def net_present_value(irr: float, cash_flows: Array, years: Array) -> float:
    """Net present value; objective function for optimizer."""
    # Note: We handle negative roots as per https://github.com/beancount/beangrow/issues/4.
    r = 1.0 + irr
    return np.sum(cash_flows / (np.sign(r) * (np.abs(r) ** years)))


def compute_dietz(
    dated_flows: List[CashFlow],
    pricer: Pricer,
    target_currency: Currency,
    end_date: Date,
) -> float:
    """
    Compute the Modified Dietz return.

     The Modified Dietz return is a method to compute the return of a series of cash
     flows. It's a time-weighted return that takes into account the time at which
    each cash flow occurs.

    Source: https://en.wikipedia.org/wiki/Modified_Dietz_method

    Formula:

    return = (B - A - F) / (A + sum(W_i * F_i))

    Where:
    B = End value
    A = Start value
    F = Sum of cash flows
    W_i = Weight of each cash flow
    F_i = Cash flow amount

    The weight of each cash flow is computed as:

    W_i = (C - D_i) / C

    Where:
    C = Number of days in the period
    D_i = Number of days from the start of the period to the date of the cash flow


    Args:
    ----
        dated_flows (List[CashFlow]): list of cash flows.
        pricer (Pricer): pricer object to convert amounts to target currency.
        target_currency (Currency): target currency.
        end_date (Date): end date of the period.

    """
    # The last cash flow is a fictitious one that represents the current position.
    # I need to remove it to compute the Dietz return.

    start_date: None | Date = None
    days_in_period: int = 1

    logging.debug("Inside Dietz. From %s to %s", start_date, end_date)

    # Array of cash flows, converted to target currency.
    usd_flows = []
    usd_weights = []
    start_value: float = 0.0
    end_value: float = 0.0
    val = 0.0
    for flow in dated_flows:
        usd_amount = -float(
            pricer.convert_amount(flow.amount, target_currency, date=flow.date).number  # type: ignore[]
        )
        if flow.source == "open":
            start_value -= usd_amount
        elif flow.source == "close":
            end_value -= usd_amount
            val -= float(flow.amount.number)  # type: ignore[]
        else:
            if start_date is None:
                logging.debug("Setting start date to %s", flow.date)
                start_date = flow.date
                days_in_period = (end_date - start_date).days

            # Formula: W_i = (C - D_i) / C
            weight = (
                days_in_period - (flow.date - start_date).days + 1
            ) / days_in_period
            usd_flows.append(usd_amount)  # type: ignore[]
            usd_weights.append(weight)

    cash_flows = np.array(usd_flows)
    weights = np.array(usd_weights)

    weight_sum = 0
    for i in range(len(cash_flows)):
        weight_sum += weights[i] * cash_flows[i]

    if end_value == 0 and start_value == 0:
        return 0.0

    # Compute the Dietz return.
    # We use:
    # End as positive, because it is a cash outflow representing the end of the period.
    # Start as positive, because it's an inflow with a minus sign. It represents the
    #   start of the period.
    pnl = end_value + start_value - np.sum(cash_flows)
    average_capital = -start_value + weight_sum
    dietz = pnl / average_capital
    logging.debug("Start date: %s", start_date)
    logging.debug("End date: %s", end_date)

    logging.debug(
        "PnL: %s + %s - %s = %s", end_value, start_value, np.sum(cash_flows), pnl
    )
    logging.debug(
        "Average capital: %s + %s = %s", -start_value, weight_sum, average_capital
    )
    logging.debug("Dietz return: %s", dietz)

    return dietz


def compute_irr(
    dated_flows: List[CashFlow],
    pricer: Pricer,
    target_currency: Currency,
    end_date: Date,
) -> float:
    """Compute the irregularly spaced IRR."""

    # Array of cash flows, converted to target currency.
    usd_flows = []
    for flow in dated_flows:
        usd_amount = pricer.convert_amount(flow.amount, target_currency, date=flow.date)
        usd_flows.append(float(usd_amount.number))  # type: ignore[]
    cash_flows = np.array(usd_flows)

    # Array of time in years.
    years = [(flow.date - end_date).days / 365 for flow in dated_flows]
    years = np.array(years)

    # Start with something reasonably normal.
    estimated_irr = 0.2 * np.sign(np.sum(cash_flows))

    # Solve for the root of the NPV equation.
    irr, *_ = fsolve(
        net_present_value, x0=estimated_irr, args=(cash_flows, years), full_output=True
    )
    return np.maximum(irr.item(), -1)


class Returns(typing.NamedTuple):
    """
    A named tuple to represent the returns of a group of cash flows.

    groupname: The name of the group of cash flows.
    first_date: The first date of the cash flows.
    last_date: The last date of the cash flows.
    years: The number of years between the first and last date.
    total: The total return.
    exdiv: The total return excluding dividends.
    div: The total return from dividends.
    flows: The list of cash flows.
    """

    groupname: str
    first_date: Date
    last_date: Date
    years: float
    total: float
    exdiv: float
    div: float
    flows: List[CashFlow]


def compute_returns(
    flows: List[CashFlow],
    pricer: Pricer,
    target_currency: Currency,
    end_date: Date,
    *,
    dietz: bool = False,
) -> Returns:
    """Compute the returns from a list of cash flows."""
    if not flows:
        return Returns("?", Date.today(), Date.today(), 0, 0, 0, 0, [])

    flows = sorted(flows, key=lambda cf: cf.date)

    if dietz:
        irr = compute_dietz(flows, pricer, target_currency, end_date)
        flows_exdiv = [flow for flow in flows if not flow.is_dividend]
        irr_exdiv = compute_dietz(flows_exdiv, pricer, target_currency, end_date)
    else:
        irr = compute_irr(flows, pricer, target_currency, end_date)
        flows_exdiv = [flow for flow in flows if not flow.is_dividend]
        irr_exdiv = compute_irr(flows_exdiv, pricer, target_currency, end_date)

    first_date = flows[0].date
    last_date = flows[-1].date
    years = (last_date - first_date).days / 365
    return Returns(
        "?", first_date, last_date, years, irr, irr_exdiv, (irr - irr_exdiv), flows
    )


def truncate_cash_flows( # noqa: C901
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
                        None
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
                        None
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


def compute_portfolio_values(
    price_map: prices.PriceMap, target_currency: Currency, transactions: data.Entries
) -> Tuple[List[Date], List[float]]:
    """Compute a serie of portfolio values over time."""

    # Infer the list of required prices.
    currency_pairs = set()
    for entry in transactions:
        for posting in entry.postings:
            if posting.meta["category"] is Cat.ASSET and posting.cost:
                currency_pairs.add((posting.units.currency, posting.cost.currency))

    first = lambda x: x[0]  # noqa: E731
    price_dates = sorted(
        itertools.chain(
            (
                (date, None)
                for pair in currency_pairs
                for date, _ in prices.get_all_prices(price_map, pair)
            ),
            ((entry.date, entry) for entry in transactions),
        ),
        key=first,
    )

    # Iterate computing the balance.
    value_dates = []
    value_values = []
    balance = Inventory()
    for date, group in itertools.groupby(price_dates, key=first):
        # Update balances.
        for _, entry in group:
            if entry is None:
                continue
            for posting in entry.postings:
                if posting.meta["category"] is Cat.ASSET:
                    balance.add_position(posting)

        # Convert to market value.
        value_balance = balance.reduce(convert.get_value, price_map, date)
        cost_balance = value_balance.reduce(
            convert.convert_position, target_currency, price_map
        )
        pos = cost_balance.get_only_position()
        value = pos.units.number if pos else ZERO

        # Add one data point.
        value_dates.append(date)
        value_values.append(value)

    return value_dates, value_values

#
# Copyright 2021-2022 Martin Blais <blais@furius.ca> and beangrow contributors
# Copyright 2022 Andreas Gerstmayr <andreas@gerstmayr.me>
#
# The following code is a derivative work of the code from the beangrow project,
# which is licensed GPLv2. This code therefore is also licensed under the terms
# of the GNU Public License, version 2.
#

import datetime
from collections import namedtuple
from typing import List, Dict, Optional, Tuple
import numpy as np
from beancount.core import data, getters, prices, convert
from beancount.core.inventory import Inventory
from beangrow import investments
import beangrow.config as configlib
import beangrow.returns as returnslib
from beangrow.reports import (
    Table,
    TODAY,
    compute_returns_table,
    get_calendar_intervals,
    get_cumulative_intervals,
    get_accounts_table,
)
from fava.ext import FavaExtensionBase
from fava.helpers import FavaAPIError
from fava.context import g

Config = namedtuple("Config", ["beangrow_config", "beangrow_debug_dir"])


class FavaPortfolioReturns(FavaExtensionBase):
    report_title = "Portfolio Returns"
    has_js_module = True

    def read_config(self) -> Config:
        if not (isinstance(self.config, dict) and "beangrow_config" in self.config):
            raise FavaAPIError(
                "Please specify a path to the beangrow configuration file."
            )

        return Config(
            beangrow_config=self.config["beangrow_config"],
            beangrow_debug_dir=self.config.get("beangrow_debug_dir"),
        )

    def extract(
        self, end_date
    ) -> Tuple[
        returnslib.Pricer, Dict, Dict[investments.Account, investments.AccountData]
    ]:
        config = self.read_config()

        entries = self.ledger.all_entries
        accounts = getters.get_accounts(entries)
        dcontext = self.ledger.options["dcontext"]

        price_map = prices.build_price_map(entries)
        pricer = returnslib.Pricer(price_map)

        beangrow_config = configlib.read_config(config.beangrow_config, None, accounts)

        # Extract data from the ledger.
        account_data_map = investments.extract(
            entries,
            dcontext,
            beangrow_config,
            end_date,
            False,
            config.beangrow_debug_dir,
        )

        return pricer, beangrow_config.groups.group, account_data_map

    @staticmethod
    def get_target_currency(adlist: List[investments.AccountData]) -> str:
        cost_currencies = set(ad.cost_currency for ad in adlist)
        if len(cost_currencies) != 1:
            raise FavaAPIError(
                "Incompatible cost currencies {} for accounts {}".format(
                    ", ".join(cost_currencies), ", ".join([ad.account for ad in adlist])
                )
            )
        return cost_currencies.pop()

    @staticmethod
    def get_only_amount(inventory):
        pos = inventory.get_only_position()
        return pos.units if pos else None

    def overview(self):
        end_date = g.filtered._date_last - datetime.timedelta(days=1)
        pricer, groups, account_data_map = self.extract(end_date)

        group_performance = []
        for group in groups:
            adlist = [
                account_data_map[name]
                for name in group.investment
                if name in account_data_map
            ]
            if not adlist:
                continue

            target_currency = group.currency
            if not target_currency:
                target_currency = self.get_target_currency(adlist)

            units = Inventory()  # commodities of this group
            cash_in_balance = Inventory()
            cash_out_balance = Inventory()

            for account_data in adlist:
                for flow in account_data.cash_flows:
                    if flow.amount.number >= 0:
                        cash_out_balance.add_amount(flow.amount)
                    else:
                        cash_in_balance.add_amount(-flow.amount)
                units.add_inventory(account_data.balance.reduce(convert.get_units))

            cash_in = self.get_only_amount(cash_in_balance)
            cash_out = self.get_only_amount(cash_out_balance)

            value_balance = units.reduce(convert.get_value, pricer.price_map, end_date)
            market_value_balance = value_balance.reduce(
                convert.convert_position, target_currency, pricer.price_map
            )
            market_value = self.get_only_amount(market_value_balance)

            returns_balance = market_value_balance + cash_out_balance + -cash_in_balance
            returns = self.get_only_amount(returns_balance)
            returns_pct = self.get_only_amount(returns_balance).number / cash_in.number

            group_performance.append(
                {
                    "name": group.name,
                    "target_currency": target_currency,
                    "cash_in": cash_in,
                    "cash_out": cash_out,
                    "market_value": market_value,
                    "returns": returns,
                    "returns_pct": returns_pct,
                    "units": units,
                }
            )

        return group_performance

    def create_plots(
        self,
        price_map: prices.PriceMap,
        target_currency: str,
        flows: List[investments.CashFlow],
        transactions: data.Entries,
        returns_rate: float,
    ) -> Dict[str, str]:
        # Render cash flows.
        cashflows_plot = {}
        dates = [f.date for f in flows]
        dates_exdiv = [f.date for f in flows if not f.is_dividend]
        dates_div = [f.date for f in flows if f.is_dividend]
        # amounts = np.array([f.amount.number for f in flows])
        amounts_exdiv = np.array([f.amount.number for f in flows if not f.is_dividend])
        amounts_div = np.array([f.amount.number for f in flows if f.is_dividend])

        cashflows_plot["exdiv"] = list(zip(dates_exdiv, amounts_exdiv))
        cashflows_plot["div"] = list(zip(dates_div, amounts_div))

        # Render cumulative cash flows, with returns growth.
        cumvalue_plot = {}
        if dates:
            date_min = dates[0] - datetime.timedelta(days=1)
            date_max = dates[-1]
            num_days = (date_max - date_min).days
            dates_all = [dates[0] + datetime.timedelta(days=x) for x in range(num_days)]
            gamounts = np.zeros(num_days)
            amounts = np.zeros(num_days)
            rate = (1 + returns_rate) ** (1.0 / 365)
            for flow in flows:
                remaining_days = (date_max - flow.date).days
                amt = -float(flow.amount.number)
                if remaining_days > 0:
                    gflow = amt * (rate ** np.arange(0, remaining_days))
                    gamounts[-remaining_days:] = np.add(
                        gamounts[-remaining_days:],
                        gflow,
                        out=gamounts[-remaining_days:],
                        casting="unsafe",
                    )
                    amounts[-remaining_days:] += amt
                else:
                    gamounts[-1] += amt
                    amounts[-1] += amt

            cumvalue_plot["gamounts"] = list(zip(dates_all, gamounts))
            cumvalue_plot["amounts"] = list(zip(dates_all, amounts))

        # Overlay value of assets over time.
        value_dates, value_values = returnslib.compute_portfolio_values(
            price_map, target_currency, transactions
        )
        cumvalue_plot["value"] = list(zip(value_dates, value_values))

        # Render PnL plot
        pnl_plot = {"value": []}
        flowsByDate = {f.date: f for f in flows}
        value_idx = 0
        spent_amount = 0
        for date in sorted(set(dates + value_dates)):
            while (
                value_idx + 1 < len(value_dates) and value_dates[value_idx + 1] <= date
            ):
                value_idx += 1

            if date in flowsByDate:
                spent_amount += -flowsByDate[date].amount.number

            # beangrow closes (virtually sells) all stocks on the last day
            market_value = value_values[value_idx] if date != dates[-1] else 0
            pnl_plot["value"].append([date, market_value - spent_amount])

        return {
            "cashflows": cashflows_plot,
            "cumvalue": cumvalue_plot,
            "pnl": pnl_plot,
            "min_date": dates[0] if dates else None,
            "max_date": dates[-1] if dates else None,
        }

    def generate_report(
        self,
        pricer: returnslib.Pricer,
        account_data: List[investments.AccountData],
        end_date: datetime.date,
        target_currency: Optional[str] = None,
    ):
        if not target_currency:
            target_currency = self.get_target_currency(account_data)

        # cash flows
        cash_flows = returnslib.truncate_and_merge_cash_flows(
            pricer, account_data, None, end_date
        )
        returns = returnslib.compute_returns(
            cash_flows, pricer, target_currency, end_date
        )
        transactions = data.sorted(
            [txn for ad in account_data for txn in ad.transactions]
        )

        # cumulative value plot
        plots = self.create_plots(
            pricer.price_map, target_currency, cash_flows, transactions, returns.total
        )

        # returns
        total_returns_tbl = Table(
            ["Total", "Ex-Div", "Div"], [[returns.total, returns.exdiv, returns.div]]
        )
        calendar_returns_tbl = compute_returns_table(
            pricer, target_currency, account_data, get_calendar_intervals(TODAY)
        )
        cumulative_returns_tbl = compute_returns_table(
            pricer, target_currency, account_data, get_cumulative_intervals(TODAY)
        )

        # accounts
        accounts_tbl = get_accounts_table(account_data)

        # cash flows
        cashflows_tbl = investments.cash_flows_to_table(cash_flows)

        return {
            "target_currency": target_currency,
            "plots": plots,
            "total_returns": total_returns_tbl,
            "calendar_returns": calendar_returns_tbl,
            "cumulative_returns": cumulative_returns_tbl,
            "accounts": accounts_tbl,
            "cashflows": cashflows_tbl,
        }

    def report(self, group_name):
        end_date = g.filtered._date_last - datetime.timedelta(days=1)
        pricer, groups, account_data_map = self.extract(end_date)

        for group in groups:
            if group.name == group_name:
                break
        else:
            raise FavaAPIError("Group not found")

        adlist = [
            account_data_map[name]
            for name in group.investment
            if name in account_data_map
        ]
        if not adlist:
            raise FavaAPIError("No transactions found in the specified time period")

        return self.generate_report(pricer, adlist, end_date, group.currency)

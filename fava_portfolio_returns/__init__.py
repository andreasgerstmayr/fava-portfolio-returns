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
from typing import List, Dict, Optional

import beangrow.config as configlib
import beangrow.returns as returnslib
import numpy as np
from beancount.core import data
from beancount.core import getters
from beancount.core import prices
from beangrow import investments
from beangrow.investments import CashFlow, AccountData
from beangrow.reports import (
    Table,
    TODAY,
    compute_returns_table,
    get_calendar_intervals,
    get_cumulative_intervals,
    get_accounts_table,
)
from beangrow.returns import Pricer
from fava.ext import FavaExtensionBase
from fava.helpers import FavaAPIException

Config = namedtuple("Config", ["beangrow_config", "beangrow_debug_dir"])


class PortfolioReturns(FavaExtensionBase):

    report_title = "Portfolio Returns"

    def _read_config(self):
        if not (isinstance(self.config, dict) and "beangrow_config" in self.config):
            raise FavaAPIException("Please specify a path to the beangrow configuration file.")

        return Config(
            beangrow_config=self.config["beangrow_config"], beangrow_debug_dir=self.config.get("beangrow_debug_dir")
        )

    def list_groups(self):
        config = self._read_config()
        entries = self.ledger.all_entries
        accounts = getters.get_accounts(entries)
        beangrow_config = configlib.read_config(config.beangrow_config, None, accounts)
        return beangrow_config.groups.group

    def _create_plots(
        self,
        price_map: prices.PriceMap,
        flows: List[CashFlow],
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
                    # gamounts[-remaining_days:] += gflow
                else:
                    gamounts[-1] += amt

            # dates[0] if dates else None, dates[-1] if dates else None)
            cumvalue_plot["gamounts"] = list(zip(dates_all, gamounts))

        # Overlay value of assets over time.
        value_dates, value_values = returnslib.compute_portfolio_values(price_map, transactions)
        cumvalue_plot["value"] = list(zip(value_dates, value_values))
        return {
            "cashflows": cashflows_plot,
            "cumvalue": cumvalue_plot,
            "min_date": dates[0] if dates else None,
            "max_date": dates[-1] if dates else None,
        }

    def _generate_report(
        self,
        pricer: Pricer,
        account_data: List[AccountData],
        end_date: datetime.date,
        target_currency: Optional[str] = None,
    ):
        if not target_currency:
            cost_currencies = set(r.cost_currency for r in account_data)
            target_currency = cost_currencies.pop()
            assert not cost_currencies, "Incompatible cost currencies {} for accounts {}".format(
                cost_currencies, ",".join([r.account for r in account_data])
            )

        # cash flows
        cash_flows = returnslib.truncate_and_merge_cash_flows(pricer, account_data, None, end_date)
        returns = returnslib.compute_returns(cash_flows, pricer, target_currency, end_date)
        transactions = data.sorted([txn for ad in account_data for txn in ad.transactions])

        # cumulative value plot
        plots = self._create_plots(pricer.price_map, cash_flows, transactions, returns.total)

        # returns
        total_returns_tbl = Table(["Total", "Ex-Div", "Div"], [[returns.total, returns.exdiv, returns.div]])
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

    def report(self, group):
        config = self._read_config()

        end_date = datetime.date.today()

        entries = self.ledger.all_entries
        accounts = getters.get_accounts(entries)
        dcontext = self.ledger.options["dcontext"]

        price_map = prices.build_price_map(entries)
        pricer = Pricer(price_map)

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

        report = next((r for r in beangrow_config.groups.group if r.name == group), None)
        if not report:
            return {}

        adlist = [account_data_map[name] for name in report.investment]
        return self._generate_report(pricer, adlist, end_date, report.currency)

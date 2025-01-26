#
# Copyright 2021-2022 Martin Blais <blais@furius.ca> and beangrow contributors
# Copyright 2025 Andreas Gerstmayr <andreas@gerstmayr.me>
#
# The following code is a derivative work of the code from the beangrow project,
# which is licensed GPLv2. This code therefore is also licensed under the terms
# of the GNU Public License, version 2.
#

import datetime
import functools
import re
import traceback
from datetime import date
from pathlib import Path
from typing import NamedTuple, Optional

from beangrow.investments import AccountData
from beangrow.returns import Pricer
from fava.context import g
from fava.ext import FavaExtensionBase, extension_endpoint
from fava.helpers import FavaAPIError
from flask import request

from fava_portfolio_returns.api.cash_flows import cash_flows_cumulative, cash_flows_list, cash_flows_table
from fava_portfolio_returns.api.dividends import get_dividends
from fava_portfolio_returns.api.portfolio import (
    portfolio_allocation,
    portfolio_cost_values,
    portfolio_market_values,
    portolio_summary,
)
from fava_portfolio_returns.api.prices import get_prices
from fava_portfolio_returns.core.intervals import (
    intervals_heatmap,
    intervals_periods,
    intervals_yearly,
    iterate_months,
    iterate_years,
)
from fava_portfolio_returns.core.portfolio import Portfolio
from fava_portfolio_returns.core.utils import get_cash_flows_time_range
from fava_portfolio_returns.returns.base import ReturnsBase
from fava_portfolio_returns.returns.irr import IRR
from fava_portfolio_returns.returns.mdm import ModifiedDietzMethod
from fava_portfolio_returns.returns.simple import SimpleReturns
from fava_portfolio_returns.returns.twr import TWR


class ExtConfig(NamedTuple):
    beangrow_config_path: Path
    beangrow_debug_dir: Optional[str]


class ToolbarContext(NamedTuple):
    investment_filter: list[str]
    """target currency"""
    target_currency: str
    """start date (inclusive)"""
    start_date: date
    """end date (inclusive)"""
    end_date: date


def api_response(func):
    """return {success: true, data: ...} or {success: false, error: ...}"""

    @functools.wraps(func)
    def decorator(*args, **kwargs):
        try:
            data = func(*args, **kwargs)
            return {"success": True, "data": data}
        except FavaAPIError as e:
            return {"success": False, "error": e.message}, 500
        except Exception as e:  # pylint: disable=broad-exception-caught
            traceback.print_exception(e)
            return {"success": False, "error": str(e)}, 500

    return decorator


class FavaPortfolioReturns(FavaExtensionBase):
    report_title = "Portfolio Returns"
    has_js_module = True

    def read_ext_config(self) -> ExtConfig:
        cfg = self.config if isinstance(self.config, dict) else {}
        beangrow_debug_dir = self.config.get("beangrow_debug_dir")
        if beangrow_debug_dir:
            beangrow_debug_dir = self.ledger.join_path(beangrow_debug_dir)

        return ExtConfig(
            beangrow_config_path=self.ledger.join_path(cfg.get("beangrow_config", "beangrow.pbtxt")),
            beangrow_debug_dir=beangrow_debug_dir,
        )

    @functools.cached_property
    def portfolio(self):
        ext_config = self.read_ext_config()
        return Portfolio(
            self.ledger.all_entries,
            self.ledger.options,
            ext_config.beangrow_config_path,
            beangrow_debug_dir=ext_config.beangrow_debug_dir,
        )

    def extract_filtered(self, toolbar_ctx: ToolbarContext):
        return self.portfolio.pricer, self.portfolio.filter_account_data_list(toolbar_ctx.investment_filter)

    def get_toolbar_ctx(self):
        sel_investments = list(filter(None, request.args.get("investments", "").split(",")))

        operating_currencies = self.ledger.options["operating_currency"]
        if len(operating_currencies) == 0:
            raise FavaAPIError("no operating currency specified in the ledger")
        currency = request.args.get("currency", operating_currencies[0])

        # pylint: disable=protected-access
        start_date = g.filtered._date_first
        # pylint: disable=protected-access
        end_date = g.filtered._date_last - datetime.timedelta(days=1)

        return ToolbarContext(
            investment_filter=sel_investments,
            target_currency=currency,
            start_date=start_date,
            end_date=end_date,
        )

    @staticmethod
    def get_target_currency(account_data_list: list[AccountData]) -> str:
        cost_currencies = set(ad.cost_currency for ad in account_data_list)
        if len(cost_currencies) != 1:
            curr = ", ".join(cost_currencies)
            accs = ", ".join([ad.account for ad in account_data_list])
            raise FavaAPIError(
                f"Found multiple cost currencies {curr} for accounts {accs}."
                " Please specify a single currency for the group in the beangrow configuration file."
            )
        return cost_currencies.pop()

    @extension_endpoint("config")  # type: ignore
    @api_response
    def api_config(self):
        operating_currencies = self.ledger.options["operating_currency"]
        if len(operating_currencies) == 0:
            raise FavaAPIError("no operating currency specified in the ledger")

        return {
            "investments": self.portfolio.investment_groups,
            "operatingCurrencies": operating_currencies,
        }

    @extension_endpoint("allocation")  # type: ignore
    @api_response
    def api_allocation(self):
        toolbar_ctx = self.get_toolbar_ctx()
        pricer, account_data_list = self.extract_filtered(toolbar_ctx)

        allocation = portfolio_allocation(pricer, account_data_list, toolbar_ctx.target_currency, toolbar_ctx.end_date)

        return {
            "allocation": allocation,
        }

    @extension_endpoint("summary")  # type: ignore
    @api_response
    def api_summary(self):
        toolbar_ctx = self.get_toolbar_ctx()
        pricer, account_data_list = self.extract_filtered(toolbar_ctx)

        _units, cash_in, cash_out, market_value, returns, returns_pct, returns_pct_annualized = portolio_summary(
            pricer, account_data_list, toolbar_ctx.target_currency, toolbar_ctx.end_date
        )
        irr = IRR().single(
            pricer, account_data_list, toolbar_ctx.target_currency, toolbar_ctx.start_date, toolbar_ctx.end_date
        )
        mdm = ModifiedDietzMethod().single(
            pricer, account_data_list, toolbar_ctx.target_currency, toolbar_ctx.start_date, toolbar_ctx.end_date
        )
        twr = TWR().single(
            pricer, account_data_list, toolbar_ctx.target_currency, toolbar_ctx.start_date, toolbar_ctx.end_date
        )

        return {
            "summary": {
                "cashIn": cash_in,
                "cashOut": cash_out,
                "marketValue": market_value,
                "returns": returns,
                "returnsPct": returns_pct,
                "returnsPctAnnualized": returns_pct_annualized,
                "irr": irr,
                "mdm": mdm,
                "twr": twr,
            },
        }

    @extension_endpoint("dividends")  # type: ignore
    @api_response
    def api_dividends(self):
        toolbar_ctx = self.get_toolbar_ctx()
        pricer, account_data_list = self.extract_filtered(toolbar_ctx)
        interval = request.args.get("interval", "monthly")

        cf_start, cf_end = get_cash_flows_time_range(account_data_list, only_dividends=True)
        start_date = max(cf_start, toolbar_ctx.start_date) if cf_start else toolbar_ctx.start_date
        end_date = min(cf_end, toolbar_ctx.end_date) if cf_end else toolbar_ctx.end_date

        if interval == "monthly":
            intervals = [f"{i.month}/{i.year}" for i in iterate_months(start_date, end_date)]
        else:
            intervals = [f"{i}" for i in iterate_years(start_date, end_date)]

        return {
            "intervals": intervals,
            "dividends": get_dividends(
                pricer,
                self.portfolio.investment_groups,
                account_data_list,
                toolbar_ctx.target_currency,
                toolbar_ctx.start_date,
                toolbar_ctx.end_date,
                interval,
            ),
        }

    @extension_endpoint("cash_flows")  # type: ignore
    @api_response
    def api_cash_flows(self):
        toolbar_ctx = self.get_toolbar_ctx()
        _pricer, account_data_list = self.extract_filtered(toolbar_ctx)

        return {
            "cashFlows": cash_flows_table(account_data_list, toolbar_ctx.start_date, toolbar_ctx.end_date),
        }

    @extension_endpoint("groups")  # type: ignore
    @api_response
    def api_groups(self):
        config = self.portfolio.beangrow_cfg
        pricer = self.portfolio.pricer
        account_data_map = self.portfolio.account_data_map
        toolbar_ctx = self.get_toolbar_ctx()

        group_performances = []
        for group in config.groups.group:  # pylint: disable=no-member
            account_data_list = [account_data_map[name] for name in group.investment if name in account_data_map]
            if not account_data_list:
                continue

            target_currency = group.currency
            if not target_currency:
                target_currency = self.get_target_currency(account_data_list)

            units, cash_in, cash_out, market_value, returns, returns_pct, returns_pct_annualized = portolio_summary(
                pricer, account_data_list, target_currency, toolbar_ctx.end_date
            )
            irr = IRR().single(pricer, account_data_list, target_currency, toolbar_ctx.start_date, toolbar_ctx.end_date)
            mdm = ModifiedDietzMethod().single(
                pricer, account_data_list, target_currency, toolbar_ctx.start_date, toolbar_ctx.end_date
            )
            twr = TWR().single(pricer, account_data_list, target_currency, toolbar_ctx.start_date, toolbar_ctx.end_date)
            group_performances.append(
                {
                    "name": group.name,
                    "currency": target_currency,
                    "units": [pos.units for pos in units],
                    "cashIn": cash_in,
                    "cashOut": cash_out,
                    "marketValue": market_value,
                    "returns": returns,
                    "returnsPct": returns_pct,
                    "returnsPctAnnualized": returns_pct_annualized,
                    "irr": irr,
                    "mdm": mdm,
                    "twr": twr,
                }
            )

        return {"groups": group_performances}

    def get_series(
        self, pricer: Pricer, account_data_list: list[AccountData], toolbar_ctx: ToolbarContext, series_name: str
    ):
        if series_name == "portfolio_market_values":
            return portfolio_market_values(
                pricer, account_data_list, toolbar_ctx.target_currency, toolbar_ctx.start_date, toolbar_ctx.end_date
            )
        elif series_name == "portfolio_cost_values":
            return portfolio_cost_values(
                pricer, account_data_list, toolbar_ctx.target_currency, toolbar_ctx.start_date, toolbar_ctx.end_date
            )
        elif m := re.match(r"^cash_flows_(div|exdiv)$", series_name):
            dividends = m.group(1) == "div"
            return cash_flows_list(
                pricer,
                account_data_list,
                toolbar_ctx.target_currency,
                toolbar_ctx.start_date,
                toolbar_ctx.end_date,
                dividends,
            )
        elif series_name == "cash_flows_cumulative":
            return cash_flows_cumulative(
                pricer,
                account_data_list,
                toolbar_ctx.target_currency,
                toolbar_ctx.start_date,
                toolbar_ctx.end_date,
            )
        elif series_name == "portfolio_returns":
            return SimpleReturns().series(
                pricer,
                account_data_list,
                toolbar_ctx.target_currency,
                toolbar_ctx.start_date,
                toolbar_ctx.end_date,
                percent=False,
            )
        elif m := re.match(r"^returns_(simple|irr|mdm|twr)_(series|heatmap|yearly|periods)$", series_name):
            method, interval = m.groups()

            fn: ReturnsBase
            if method == "simple":
                fn = SimpleReturns()
            elif method == "irr":
                fn = IRR()
            elif method == "mdm":
                fn = ModifiedDietzMethod()
            elif method == "twr":
                fn = TWR()
            else:
                raise FavaAPIError(f"Invalid method {method}")

            if interval == "series":
                return fn.series(
                    pricer,
                    account_data_list,
                    toolbar_ctx.target_currency,
                    toolbar_ctx.start_date,
                    toolbar_ctx.end_date,
                )

            cf_start, _ = get_cash_flows_time_range(account_data_list)
            if interval == "heatmap":
                # skip time before first cash flow
                start_date = max(cf_start, toolbar_ctx.start_date) if cf_start else toolbar_ctx.start_date
                intervals = intervals_heatmap(start_date.year, toolbar_ctx.end_date.year)
            elif interval == "yearly":
                intervals = intervals_yearly(toolbar_ctx.end_date)
            elif interval == "periods":
                # the 'MAX' interval should start at the first cash flow, not at the date range selection
                # use toolbar_ctx.start_date in case cf_start is None (no cash flow found)
                intervals = intervals_periods(cf_start or toolbar_ctx.start_date, toolbar_ctx.end_date)
            else:
                raise FavaAPIError(f"Invalid interval {interval}")

            return fn.intervals(
                pricer,
                account_data_list,
                toolbar_ctx.target_currency,
                intervals,
            )
        elif m := re.match(r"^price_(.+)$", series_name):
            currency = m.group(1)
            return get_prices(pricer, toolbar_ctx.target_currency, currency)
        else:
            raise FavaAPIError(f"Invalid series name {series_name}")

    @extension_endpoint("series")  # type: ignore
    @api_response
    def api_series(self):
        """
        a generic endpoint to return one or multiple series (a list of x,y tuples)
        for the given investments and start and end date
        """
        toolbar_ctx = self.get_toolbar_ctx()
        pricer, account_data_list = self.extract_filtered(toolbar_ctx)
        requested_series = list(filter(None, request.args.get("series", "").split(",")))

        series = {}
        for series_name in requested_series:
            series[series_name] = self.get_series(pricer, account_data_list, toolbar_ctx, series_name)

        return {"series": series}

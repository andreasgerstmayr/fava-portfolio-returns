import datetime
import functools
import logging
import os
import traceback
from datetime import date
from pathlib import Path
from typing import NamedTuple
from typing import Optional

from fava.beans.abc import Directive
from fava.beans.abc import Price
from fava.beans.abc import Transaction
from fava.context import g
from fava.ext import FavaExtensionBase
from fava.ext import extension_endpoint
from fava.helpers import FavaAPIError
from flask import request

from fava_portfolio_returns.api.cash_flows import cash_flows_chart
from fava_portfolio_returns.api.cash_flows import cash_flows_table
from fava_portfolio_returns.api.cash_flows import dividends_chart
from fava_portfolio_returns.api.compare import compare_chart
from fava_portfolio_returns.api.investments import investments_group_by_currency
from fava_portfolio_returns.api.investments import investments_group_by_group
from fava_portfolio_returns.api.portfolio import portfolio_allocation
from fava_portfolio_returns.api.portfolio import portfolio_values
from fava_portfolio_returns.core.intervals import intervals_heatmap
from fava_portfolio_returns.core.intervals import intervals_periods
from fava_portfolio_returns.core.intervals import intervals_yearly
from fava_portfolio_returns.core.portfolio import Portfolio
from fava_portfolio_returns.returns.factory import RETURN_METHODS
from fava_portfolio_returns.returns.monetary import MonetaryReturns

logger = logging.getLogger(__name__)
if loglevel := os.environ.get("LOGLEVEL"):
    logger.setLevel(loglevel.upper())


class ExtConfig(NamedTuple):
    beangrow_config_path: Path
    beangrow_debug_dir: Optional[Path]
    pnl_color_scheme: Optional[str]


class ToolbarContext(NamedTuple):
    investment_filter: list[str]
    """target currency"""
    target_currency: str
    """start date of the current date filter, or first transaction date of the ledger (inclusive)"""
    start_date: date
    """end date of the current date filter, or last transaction date of the ledger (inclusive)"""
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
    cached_portfolio: Optional[Portfolio]

    def after_load_file(self) -> None:
        """Fava hook which runs after a ledger file has been (re-)loaded"""
        # clear cache
        self.cached_portfolio = None

    def read_ext_config(self) -> ExtConfig:
        cfg = self.config if isinstance(self.config, dict) else {}
        beangrow_debug_dir = cfg.get("beangrow_debug_dir")
        if beangrow_debug_dir:
            beangrow_debug_dir = self.ledger.join_path(beangrow_debug_dir)

        pnl_color_scheme_value = cfg.get("pnl_color_scheme", None)

        return ExtConfig(
            beangrow_config_path=self.ledger.join_path(cfg.get("beangrow_config", "beangrow.pbtxt")),
            beangrow_debug_dir=beangrow_debug_dir,
            pnl_color_scheme=pnl_color_scheme_value,
        )

    def get_ledger_duration(self, entries: list[Directive]):
        date_first = None
        date_last = None
        for entry in entries:
            if isinstance(entry, Transaction):
                date_first = entry.date
                break
        for entry in reversed(entries):
            if isinstance(entry, (Transaction, Price)):
                date_last = entry.date
                break
        if not date_first or not date_last:
            raise FavaAPIError("no transaction found")
        return (date_first, date_last)

    def get_toolbar_ctx(self):
        sel_investments = list(filter(None, request.args.get("investments", "").split(",")))

        operating_currencies = self.ledger.options["operating_currency"]
        if len(operating_currencies) == 0:
            raise FavaAPIError("No operating currency specified in the ledger")
        currency = request.args.get("currency", operating_currencies[0])

        if g.filtered.date_range:
            filter_first = g.filtered.date_range.begin
            filter_last = g.filtered.date_range.end - datetime.timedelta(days=1)
            # Use filtered ledger here, as another filter (e.g. tag filter) could be applied.
            ledger_date_first, ledger_date_last = self.get_ledger_duration(g.filtered.entries_with_all_prices)

            # Adjust the dates in case the date filter is set to e.g. 2023-2024,
            # however the ledger only contains data up to summer 2024.
            # Without this, a wrong number of days between start_date and end_date is calculated.

            # First, check if there is an overlap between ledger and filter dates
            if filter_last < ledger_date_first or filter_first > ledger_date_last:
                # If there is no overlap of ledger and filter dates, leave them as-is.
                # For example filter: 2020-2021, but ledger data goes from 2022-2023.
                # Using min/max here would give from max(2020,2022) until min(2021,2023) = from 2022 until 2021, which is invalid.
                date_first = filter_first
                date_last = filter_last
            else:
                # If there is overlap between ledger and filter dates, use min/max
                date_first = max(filter_first, ledger_date_first)
                date_last = min(filter_last, ledger_date_last)
        else:
            # No time filter applied.
            # Use filtered ledger here, as another filter (e.g. tag filter) could be applied.
            date_first, date_last = self.get_ledger_duration(g.filtered.entries_with_all_prices)

        return ToolbarContext(
            investment_filter=sel_investments,
            target_currency=currency,
            start_date=date_first,
            end_date=date_last,
        )

    def get_portfolio(self):
        if not self.cached_portfolio:
            ext_config = self.read_ext_config()
            self.cached_portfolio = Portfolio(
                self.ledger.all_entries,
                self.ledger.options,
                ext_config.beangrow_config_path,
                beangrow_debug_dir=ext_config.beangrow_debug_dir,
            )
        return self.cached_portfolio

    def get_filtered_portfolio(self, toolbar_ctx: ToolbarContext):
        return self.get_portfolio().filter(toolbar_ctx.investment_filter, toolbar_ctx.target_currency)

    @extension_endpoint("config")
    @api_response
    def api_config(self):
        portfolio = self.get_portfolio()
        ext_config = self.read_ext_config()

        operating_currencies = self.ledger.options["operating_currency"]
        if len(operating_currencies) == 0:
            raise FavaAPIError("no operating currency specified in the ledger")

        return {
            "investmentsConfig": portfolio.investments_config,
            "operatingCurrencies": operating_currencies,
            "pnlColorScheme": ext_config.pnl_color_scheme,
        }

    @extension_endpoint("portfolio")
    @api_response
    def api_portfolio(self):
        toolbar_ctx = self.get_toolbar_ctx()
        p = self.get_filtered_portfolio(toolbar_ctx)

        value_chart = portfolio_values(p, toolbar_ctx.start_date, toolbar_ctx.end_date)
        performance_chart = MonetaryReturns().series(p, toolbar_ctx.start_date, toolbar_ctx.end_date)
        allocation = portfolio_allocation(p, toolbar_ctx.end_date)

        return {
            "valueChart": value_chart,
            "performanceChart": performance_chart,
            "allocation": allocation,
        }

    @extension_endpoint("compare")
    @api_response
    def api_compare(self):
        toolbar_ctx = self.get_toolbar_ctx()
        p = self.get_filtered_portfolio(toolbar_ctx)
        method = request.args.get("method", "")
        compare_with = list(filter(None, request.args.get("compareWith", "").split(",")))

        series = compare_chart(p, toolbar_ctx.start_date, toolbar_ctx.end_date, method, compare_with)

        return {"series": series}

    @extension_endpoint("returns")
    @api_response
    def api_returns(self):
        toolbar_ctx = self.get_toolbar_ctx()
        p = self.get_filtered_portfolio(toolbar_ctx)
        method = request.args.get("method", "")
        interval = request.args.get("interval", "")

        returns_method = RETURN_METHODS.get(method)
        if not returns_method:
            raise FavaAPIError(f"Invalid method {method}")

        cash_flows = p.cash_flows()
        if cash_flows and toolbar_ctx.start_date <= cash_flows[0].date <= toolbar_ctx.end_date:
            # skip time before first cash flow
            start_date = cash_flows[0].date
        else:
            start_date = toolbar_ctx.start_date

        if interval == "heatmap":
            intervals = intervals_heatmap(start_date, toolbar_ctx.end_date)
        elif interval == "yearly":
            intervals = intervals_yearly(start_date, toolbar_ctx.end_date)
        elif interval == "periods":
            intervals = intervals_periods(start_date, toolbar_ctx.end_date)
        else:
            raise FavaAPIError(f"Invalid interval {interval}")

        return {"returns": returns_method.intervals(p, intervals)}

    @extension_endpoint("dividends")
    @api_response
    def api_dividends(self):
        toolbar_ctx = self.get_toolbar_ctx()
        p = self.get_filtered_portfolio(toolbar_ctx)
        interval = request.args.get("interval", "monthly")

        chart = dividends_chart(p, toolbar_ctx.start_date, toolbar_ctx.end_date, interval)
        return {
            "chart": chart,
        }

    @extension_endpoint("cash_flows")
    @api_response
    def api_cash_flows(self):
        toolbar_ctx = self.get_toolbar_ctx()
        p = self.get_filtered_portfolio(toolbar_ctx)
        interval = request.args.get("interval", "monthly")

        chart = cash_flows_chart(p, toolbar_ctx.start_date, toolbar_ctx.end_date, interval)
        table = cash_flows_table(p, toolbar_ctx.start_date, toolbar_ctx.end_date)
        return {
            "chart": chart,
            "table": table,
        }

    @extension_endpoint("investments")
    @api_response
    def api_investments(self):
        p = self.get_portfolio()
        toolbar_ctx = self.get_toolbar_ctx()
        group_by = request.args.get("group_by", "group")

        if group_by == "group":
            return {"investments": list(investments_group_by_group(p, toolbar_ctx.start_date, toolbar_ctx.end_date))}
        elif group_by == "currency":
            return {
                "investments": list(
                    investments_group_by_currency(
                        p, toolbar_ctx.target_currency, toolbar_ctx.start_date, toolbar_ctx.end_date
                    )
                )
            }
        else:
            raise FavaAPIError(f"Invalid group by {group_by}")

    @extension_endpoint("missing_prices")
    @api_response
    def api_missing_prices(self):
        p = self.get_portfolio()

        missing_prices, commands = p.get_missing_prices()
        return {"missingPrices": missing_prices, "commands": commands}

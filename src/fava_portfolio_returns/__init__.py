import datetime
import functools
import logging
import os
import traceback
from datetime import date
from pathlib import Path
from typing import NamedTuple
from typing import Optional

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

        return ExtConfig(
            beangrow_config_path=self.ledger.join_path(cfg.get("beangrow_config", "beangrow.pbtxt")),
            beangrow_debug_dir=beangrow_debug_dir,
        )

    def get_toolbar_ctx(self):
        sel_investments = list(filter(None, request.args.get("investments", "").split(",")))

        operating_currencies = self.ledger.options["operating_currency"]
        if len(operating_currencies) == 0:
            raise FavaAPIError("No operating currency specified in the ledger")
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

        operating_currencies = self.ledger.options["operating_currency"]
        if len(operating_currencies) == 0:
            raise FavaAPIError("no operating currency specified in the ledger")

        return {
            "investments": portfolio.investment_groups,
            "operatingCurrencies": operating_currencies,
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
        cf_start = cash_flows[0].date if cash_flows else None

        if interval == "heatmap":
            # skip time before first cash flow in case start_date is before cf_start
            start_date = max(cf_start, toolbar_ctx.start_date) if cf_start else toolbar_ctx.start_date
            intervals = intervals_heatmap(start_date.year, toolbar_ctx.end_date.year)
        elif interval == "yearly":
            intervals = intervals_yearly(toolbar_ctx.end_date)
        elif interval == "periods":
            # start_date is only used for the 'MAX' interval, which should start at the first cash flow, not at the date range selection
            # use toolbar_ctx.start_date in case cf_start is None (no cash flow found)
            intervals = intervals_periods(cf_start or toolbar_ctx.start_date, toolbar_ctx.end_date)
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

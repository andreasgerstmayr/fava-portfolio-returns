#!/usr/bin/env python3
"""
Calculate my true returns, including dividends and real costs.
"""

__copyright__ = "Copyright (C) 2020  Martin Blais"
__license__ = "GNU GPLv2"

import collections
import datetime
import io
import logging
import multiprocessing
import platform
import subprocess
import tempfile
import typing
from functools import partial
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

#import matplotlib.dates as mdates
#import matplotlib.pyplot as plt
import numpy as np
#import pandas as pd
from beancount.core import data, prices
from beancount.core.amount import Amount
from beancount.parser import printer
from dateutil.relativedelta import relativedelta
#from matplotlib.axes import Axes
#from pandas.plotting import register_matplotlib_converters

from fava_portfolio_returns._vendor.beangrow import investments
from fava_portfolio_returns._vendor.beangrow import returns as returnslib
from fava_portfolio_returns._vendor.beangrow.config_pb2 import Config, Group
from fava_portfolio_returns._vendor.beangrow.investments import AccountData, CashFlow
from fava_portfolio_returns._vendor.beangrow.returns import Pricer

#register_matplotlib_converters()

# Basic type aliases.
Account = str
Currency = str
Date = datetime.date
Array = np.ndarray


# The date at which we evaluate this.
TODAY = Date.today()


CurrencyPair = Tuple[Currency, Currency]


IRR_FORMAT = "{:32}: {:6.2%} ({:6.2%} ex-div, {:6.2%} div)"


STYLE = """
@media print {
    @page { margin: 0in; }
    body { margin: 0.2in; }
    .new-page { page-break-before: always; }
}

body, table { font: 9px Noto Sans, sans-serif; }

p { margin: 0.2em; }

table { border-collapse: collapse; }
table td, table th { border: thin solid black; }

table.full { width: 100%; }

/* p { margin-bottom: .1em } */
"""

RETURNS_TEMPLATE_PRE = """
<html>
  <head>
    <title>{title}</title>
    <link href="https://fonts.googleapis.com/css2?family=Noto+Sans&display=swap"
     rel="stylesheet">

    <style>
      {style}
    </style>
  <head>
    <body>
      <h1>{title}</h1>
"""
RETURNS_TEMPLATE_POST = """
    </body>
</html>
"""


class Table(typing.NamedTuple):
    """
    Table to be rendered to HTML.
    """

    header: List[str]
    rows: List[List[Any]]


def render_table(
    table: Table, floatfmt: Optional[str] = None, classes: Optional[List[str]] = None
) -> str:
    """Render a simple data table to HTML."""
    oss = io.StringIO()
    fprint = partial(print, file=oss)
    fprint('<table class="{}">'.format(" ".join(classes or [])))
    fprint("<tr>")
    for heading in table.header:
        fprint(f"<th>{heading}</th>")
    fprint("</tr>")
    for row in table.rows:
        fprint("<tr>")
        for value in row:
            if isinstance(value, float) and floatfmt:
                value = floatfmt.format(value)  # noqa: PLW2901
            fprint(f"<td>{value}</td>")
        fprint("</tr>")
    fprint("</table>")
    return oss.getvalue()


# A named date interval: (name, start date, end date).
Interval = Tuple[str, Date, Date]


def compute_returns_table(
    pricer: Pricer,
    target_currency: Currency,
    account_data: List[AccountData],
    intervals: List[Interval],
    *,
    header_text: str = "Return",
    dietz: bool = False,
) -> Table:
    """Compute a table of sequential returns."""
    header = [header_text]
    rows: List[list[str | float]] = [["Total"], ["Ex-div"], ["Div"]]
    for intname, date1, date2 in intervals:
        header.append(intname)
        cash_flows = returnslib.truncate_and_merge_cash_flows(
            pricer, account_data, date1, date2
        )
        returns = returnslib.compute_returns(
            cash_flows, pricer, target_currency, date2, dietz=dietz
        )
        rows[0].append(returns.total)
        rows[1].append(returns.exdiv)
        rows[2].append(returns.div)
    return Table(header, rows)


def write_returns_pdf(
    pdf_filename: str,
    *args,  # noqa: ANN002
    **kwargs,  # noqa: ANN003
) -> None:
    """Write out returns for a combined list of account account_data.."""
    logging.info("Writing returns file: %s", pdf_filename)

    with tempfile.TemporaryDirectory() as tmpdir:
        indexfile = write_returns_html(tmpdir, *args, **kwargs)
        command = [
            "google-chrome",
            "--headless",
            "--disable-gpu",
            f"--print-to-pdf={pdf_filename}",
            indexfile,
        ]
        subprocess.check_call(
            command,  # noqa: S603
            stderr=open("/dev/null", "w"),  # noqa: SIM115, PTH123
        )
        if not Path.exists(Path(pdf_filename)):
            msg = f"Failed to produce PDF: {pdf_filename}"
            raise RuntimeError(msg)
        logging.info("Done: file://%s", pdf_filename)


def write_returns_html(  # noqa: PLR0913
    dirname: str,
    pricer: Pricer,
    account_data: List[AccountData],
    title: str,
    end_date: Date,
    target_currency: Optional[Currency] = None,
) -> str:
    """Write out returns report to a directory with files in it."""

    logging.info("Writing returns dir for %s: %s", title, dirname)
    Path(dirname).mkdir(parents=True, exist_ok=True)
    with Path(Path(dirname) / "index.html").open("w", encoding="utf8") as indexfile:
        fprint = partial(print, file=indexfile)
        fprint(RETURNS_TEMPLATE_PRE.format(style=STYLE, title=title))

        if not target_currency:
            cost_currencies = {r.cost_currency for r in account_data}
            target_currency = cost_currencies.pop()

            # assert (
            #     not cost_currencies
            # ), "Incompatible cost currencies {} for accounts {}".format(
            #     cost_currencies, ",".join([r.account for r in account_data])
            # )

            if cost_currencies:
                msg = "Incompatible cost currencies {} for accounts {}".format(
                    cost_currencies, ",".join([r.account for r in account_data])
                )
                raise ValueError(msg)

        # TOOD(blais): Prices should be plot separately, by currency.
        # fprint("<h2>Prices</h2>")
        # pairs = set((r.currency, r.cost_currency) for r in account_data)
        # plots = plot_prices(dirname, pricer.price_map, pairs)
        # for _, filename in sorted(plots.items()):
        #     fprint('<img src={} style="width: 100%"/>'.format(filename))

        fprint("<h2>Cash Flows</h2>")

        cash_flows = returnslib.truncate_and_merge_cash_flows(
            pricer, account_data, None, end_date
        )
        returns = returnslib.compute_returns(
            cash_flows, pricer, target_currency, end_date
        )

        returns_dietz = returnslib.compute_returns(
            cash_flows, pricer, target_currency, end_date, dietz=True
        )

        transactions = data.sorted(
            [txn for ad in account_data for txn in ad.transactions]
        )

        # Note: This is where the vast majority of the time is spent.
        plots = plot_flows(
            dirname,
            pricer.price_map,
            target_currency,
            cash_flows,
            transactions,
            returns.total,
        )
        fprint('<img src={} style="width: 100%"/>'.format(plots["flows"]))
        fprint('<img src={} style="width: 100%"/>'.format(plots["cumvalue"]))

        fprint("<h2>Total returns</h2>")

        fprint("<h3>Internal Rate of Return (IRR)</h3>")
        fprint(
            render_table(
                Table(
                    ["Total", "Ex-Div", "Div"],
                    [[returns.total, returns.exdiv, returns.div]],
                ),
                floatfmt="{:.2%}",
            )
        )

        fprint("<h3>Modified Dietz return (MDRR)</h3>")
        fprint(
            render_table(
                Table(
                    ["Total", "Ex-Div", "Div"],
                    [[returns_dietz.total, returns_dietz.exdiv, returns_dietz.div]],
                ),
                floatfmt="{:.2%}",
            )
        )

        fprint("<h2>Annualized returns</h2>")

        fprint("<h3>Internal Rate of Return (IRR)</h3>")
        # Compute table of returns over intervals.
        table = compute_returns_table(
            pricer, target_currency, account_data, get_calendar_intervals(TODAY)
        )
        fprint("<p>", render_table(table, floatfmt="{:.1%}", classes=["full"]), "</p>")

        fprint("<h3>Modified Dietz return (MDRR)</h3>")
        table = compute_returns_table(
            pricer,
            target_currency,
            account_data,
            get_calendar_intervals(TODAY),
            dietz=True,
        )
        fprint("<p>", render_table(table, floatfmt="{:.1%}", classes=["full"]), "</p>")

        fprint("<h2>Cumulative returns</h2>")

        fprint("<h3>Internal Rate of Return (IRR)</h3>")
        table = compute_returns_table(
            pricer, target_currency, account_data, get_cumulative_intervals(TODAY)
        )
        fprint("<p>", render_table(table, floatfmt="{:.1%}", classes=["full"]), "</p>")

        fprint("<h3>Modified Dietz return (MDRR)</h3>")
        table = compute_returns_table(
            pricer,
            target_currency,
            account_data,
            get_cumulative_intervals(TODAY),
            dietz=True,
        )
        fprint("<p>", render_table(table, floatfmt="{:.1%}", classes=["full"]), "</p>")

        fprint('<h2 class="new-page">Accounts</h2>')
        fprint(f"<p>Cost Currency: {target_currency}</p>")
        accounts_df = get_accounts_table(account_data)
        fprint(accounts_df.to_html())

        fprint('<h2 class="new-page">Cash Flows</h2>')
        df_cash_flows = investments.cash_flows_to_table(cash_flows)
        fprint(df_cash_flows.to_html())

        fprint(RETURNS_TEMPLATE_POST)

    return indexfile.name


def write_returns_debugfile(
    filename: str,
    pricer: Pricer,
    account_data: List[AccountData],
    title: str,
    end_date: Date,
    _: Optional[Currency] = None,
) -> str:
    """Write out returns report to a directory with files in it."""

    logging.info("Writing returns dir for %s: %s", title, filename)
    Path(filename).parent.mkdir(parents=True, exist_ok=True)

    with Path(filename).open("w", encoding="utf8") as indexfile:
        fprint = partial(print, file=indexfile)
        fprint(f"* {title}")
        fprint("** Cash Flows")
        fprint()
        cash_flows = returnslib.truncate_and_merge_cash_flows(
            pricer, account_data, None, end_date
        )
        df_cash_flows = investments.cash_flows_to_table(cash_flows)
        fprint(df_cash_flows.to_string())

    return indexfile.name


def get_accounts_table(account_data: List[AccountData]):
    """Build of table of per-account information."""
    header = ["Investment", "Description", "Status"]
    rows = []
    for ad in account_data:
        if ad.close is not None:
            status_str = "Closed"
        elif ad.balance.is_empty():
            status_str = "Empty"
        else:
            status_str = "Active"

        name = (
            ad.commodity.meta.get("name", ad.commodity.currency)
            if ad.commodity
            else "N/A"
        )
        rows.append((ad.account, name, status_str))
    return pd.DataFrame(data=rows, columns=header)


def set_axis(
    ax_,
    date_min: Date,
    date_max: Date,
) -> None:
    """Set up X axis for dates."""

    years = mdates.YearLocator()
    years_fmt = mdates.DateFormatter("%Y")
    months = mdates.MonthLocator()

    ax_.xaxis.set_major_locator(years)
    ax_.xaxis.set_major_formatter(years_fmt)
    ax_.xaxis.set_minor_locator(months)

    if date_min and date_max:
        datemin = np.datetime64(date_min, "Y")
        datemax = np.datetime64(date_max, "Y") + np.timedelta64(1, "Y")
        ax_.set_xlim(datemin, datemax)  # type: ignore[]

    ax_.format_xdata = mdates.DateFormatter("%Y-%m-%d")
    ax_.format_ydata = "{:,}".format
    ax_.grid(visible=True)


def plot_prices(
    output_dir: str, price_map: prices.PriceMap, pairs: List[CurrencyPair]
) -> Dict[str, str]:
    """Render one or more plots of prices."""

    # Group by quote currencies.
    outplots = {}
    series = collections.defaultdict(list)
    for currency, quote_currency in pairs:
        series[quote_currency].append(currency)

    fig, axs = plt.subplots(len(series), 1, sharex=True, figsize=[10, 2 * len(series)])
    if len(series) == 1:
        axs = [axs]
    for index, (qc, currencies) in enumerate(sorted(series.items())):
        ax = axs[index]
        for currency in currencies:
            price_points = prices.get_all_prices(price_map, (currency, qc))

            # Render cash flows.
            dates = [date for date, _ in price_points]
            prices_ = [float(price) for _, price in price_points]

            set_axis(ax, dates[0] if dates else None, dates[-1] if dates else None)  # type: ignore[]
            ax.plot(dates, prices_, linewidth=0.3)  # type: ignore[]
            ax.scatter(dates, prices_, s=1.2)  # type: ignore[]

    fig.autofmt_xdate()
    fig.tight_layout()
    # filename = outplots["price"] = path.join(output_dir, "price.svg")
    filename = outplots["price"] = Path(output_dir) / "price.svg"
    plt.savefig(filename)
    plt.close(fig)

    return outplots


def plot_flows(  # noqa: PLR0915, PLR0913
    output_dir: str,
    price_map: prices.PriceMap,
    target_currency: Currency,
    flows: List[CashFlow],
    transactions: data.Entries,
    returns_rate: float,
) -> Dict[str, str]:
    """Produce plots from cash flows and returns, and more."""

    # Render cash flows.
    outplots = {}
    dates = [f.date for f in flows]
    dates_exdiv = [f.date for f in flows if not f.is_dividend]
    dates_div = [f.date for f in flows if f.is_dividend]
    # amounts = np.array([f.amount.number for f in flows])
    amounts_exdiv = np.array([f.amount.number for f in flows if not f.is_dividend])
    amounts_div = np.array([f.amount.number for f in flows if f.is_dividend])

    ax: Axes
    fig, axs = plt.subplots(
        2, 1, sharex=True, figsize=[10, 4], gridspec_kw={"height_ratios": [3, 1]}
    )
    for ax in axs:
        set_axis(ax, dates[0] if dates else None, dates[-1] if dates else None)  # type: ignore[]
        ax.axhline(0, color="#000", linewidth=0.2)
        ax.vlines(dates_exdiv, 0, amounts_exdiv, linewidth=3, color="#000", alpha=0.7)  # type: ignore[]
        ax.vlines(dates_div, 0, amounts_div, linewidth=3, color="#0A0", alpha=0.7)  # type: ignore[]
    axs[1].set_yscale("symlog")

    axs[0].set_title("Cash Flows")
    axs[1].set_title("log(Cash Flows)")
    fig.autofmt_xdate()
    fig.tight_layout()
    filename = Path(output_dir) / "flows.svg"
    outplots["flows"] = "flows.svg"
    plt.savefig(filename)
    plt.close(fig)

    # Render cumulative cash flows, with returns growth.
    lw = 0.8

    if dates:
        date_min = dates[0] - datetime.timedelta(days=1)
        date_max = dates[-1]
        num_days = (date_max - date_min).days
        dates_all = [dates[0] + datetime.timedelta(days=x) for x in range(num_days)]
        gamounts = np.zeros(num_days)
        rate = (1 + returns_rate) ** (1.0 / 365)
        for flow in flows:
            remaining_days = (date_max - flow.date).days
            amt = -float(flow.amount.number)  # type: ignore[]
            if remaining_days > 0:
                gflow = amt * (rate ** np.arange(0, remaining_days))
                gamounts[-remaining_days:] += gflow
            else:
                gamounts[-1] += amt

        fig, ax = plt.subplots(figsize=[10, 4])
        ax.set_title("Cumulative value")
        set_axis(ax, dates[0] if dates else None, dates[-1] if dates else None)  # type: ignore[]
        ax.axhline(0, color="#000", linewidth=lw)

        # ax.scatter(dates_all, gamounts, color='#000', alpha=0.2, s=1.0)
        ax.plot(dates_all, gamounts, color="#000", alpha=0.7, linewidth=lw)

        # Overlay value of assets over time.
        value_dates, value_values = returnslib.compute_portfolio_values(
            price_map, target_currency, transactions
        )

        ax.plot(value_dates, value_values, color="#00F", alpha=0.5, linewidth=lw)
        ax.scatter(value_dates, value_values, color="#00F", alpha=lw, s=2)  # type: ignore[]
        ax.legend(["Amortized value from flows", "Market value"], fontsize="xx-small")

        fig.autofmt_xdate()
        fig.tight_layout()
        filename = Path(output_dir) / "cumvalue.svg"
        outplots["cumvalue"] = "cumvalue.svg"
        plt.savefig(filename)
        plt.close(fig)

    return outplots


def write_price_directives(
    filename: str, pricer: Pricer, days_price_threshold: int
) -> None:
    """Write a list of required price directives as a Beancount file."""
    price_entries = []
    for (currency, required_date), found_dates in sorted(
        pricer.required_prices.items()
    ):
        if len(found_dates) != 1:
            msg = f"Found multiple prices for {currency} on {required_date}: {found_dates}"  # noqa: E501
            raise ValueError(msg)

        cost_currency, actual_date, rate = found_dates.pop()
        days_late = (required_date - actual_date).days
        if days_late < days_price_threshold:
            continue
        price = data.Price({}, required_date, currency, Amount(rate, cost_currency))  # type: ignore[]
        price_entries.append(price)

    Path(filename).parent.mkdir(parents=True, exist_ok=True)
    with Path(filename).open("w", encoding="utf8") as prfile:
        printer.print_entries(price_entries, file=prfile)


def get_calendar_intervals(date: Date) -> List[Interval]:
    """Return a list of date pairs for sequential intervals."""
    intervals = [
        (str(year), Date(year, 1, 1), Date(year + 1, 1, 1))
        for year in range(date.year - 15, date.year)
    ]
    intervals.append((str(date.year), Date(date.year, 1, 1), date))
    return intervals


def get_cumulative_intervals(date: Date) -> List[Interval]:
    """Return a list of date pairs for sequential intervals."""
    return [
        ("15 years ago", Date(date.year - 15, 1, 1), date),
        ("10 years ago", Date(date.year - 10, 1, 1), date),
        ("5 years ago", Date(date.year - 5, 1, 1), date),
        ("4 years ago", Date(date.year - 4, 1, 1), date),
        ("3 years ago", Date(date.year - 3, 1, 1), date),
        ("2 years ago", Date(date.year - 2, 1, 1), date),
        ("1 year ago", Date(date.year - 1, 1, 1), date),
        ("YTD", Date(date.year, 1, 1), date),
        ("rolling 6 months ago", date - relativedelta(months=6), date),
        ("rolling 3 months ago", date - relativedelta(months=3), date),
    ]


def generate_reports(  # noqa: PLR0913
    account_data_map: Dict[Account, AccountData],
    config: Config,  # type: ignore[]
    price_map: prices.PriceMap,
    end_date: Date,
    output_dir: str,
    *,
    parallel: bool,
    pdf: bool,
) -> Pricer:
    """Produce the list of requested reports."""

    pricer = Pricer(price_map)

    # Write out a returns file for every account.
    # os.makedirs(output_dir, exist_ok=True)
    multiprocessing.set_start_method(
        "spawn" if platform.system() == "Windows" else "fork"
    )
    calls = []
    for report in config.groups.group:
        adlist = [account_data_map[name] for name in report.investment]

        if not isinstance(adlist, list):
            msg = f"Expected list, got {type(adlist)}"
            raise TypeError(msg)

        if not all(isinstance(ad, AccountData) for ad in adlist):
            msg = f"Expected list of AccountData, got {adlist}"
            raise TypeError(msg)

        function = write_returns_pdf if pdf else write_returns_html
        basename = Path(output_dir) / report.name
        filename = f"{basename}.pdf" if pdf else basename
        calls.append(
            partial(
                function,
                filename,
                pricer,
                adlist,
                report.name,
                end_date,
                report.currency,
            )
        )

        calls.append(
            partial(
                write_returns_debugfile,
                f"{basename}.org",
                pricer,
                adlist,
                report.name,
                end_date,
                report.currency,
            )
        )

    if parallel:
        with multiprocessing.Pool(5) as pool:
            asyns = [pool.apply_async(func) for func in calls]
            for asyn in asyns:
                asyn.wait()
                if not asyn.successful():
                    msg = f"Failed to produce report: {asyn.get()}"
                    raise RuntimeError(msg)
    else:
        for func in calls:
            func()

    return pricer


def generate_report_mapper(
    item: Tuple[Group, List[AccountData]],  # type: ignore[]
    price_map: prices.PriceMap,
    end_date: Date,
) -> Tuple[str, bytes]:
    """A mapper function that can be run from Beam to produce a PDF's bytes."""  # noqa: D401
    report, adlist = item
    with tempfile.NamedTemporaryFile("wb") as tmpfile:
        pricer = Pricer(price_map)
        write_returns_pdf(
            tmpfile.name, pricer, adlist, report.name, end_date, report.currency
        )
        tmpfile.flush()
        with Path(tmpfile.name).open("rb") as rfile:
            return (report.name, rfile.read())


def generate_price_pages(
    account_data_map: Dict[Account, AccountData],
    price_map: prices.PriceMap,
    output_dir: str,
) -> None:
    """
    Produce renders of price time series for each currency.

    This should help us debug issues with price recording, in particulawr,
    with respect to stock splits.
    """
    # Write out a returns file for every account.
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    pairs = {
        (ad.currency, ad.cost_currency)
        for ad in account_data_map.values()
        if ad.currency and ad.cost_currency
    }

    for base_quote in sorted(pairs):
        logging.info("Producing price page for %s", base_quote)
        all_prices = prices.get_all_prices(price_map, base_quote)
        if not all_prices:
            continue

        dates = np.array([date for date, _ in all_prices])
        prices_ = np.array([price for _, price in all_prices])

        fig, ax = plt.subplots(1, 1, figsize=[10, 4])
        set_axis(ax, dates[0], dates[-1])
        ax.set_title("Prices for {} ({})".format(*base_quote))
        ax.plot(dates, prices_, linewidth=0.5)
        ax.scatter(dates, prices_, s=2.0)
        fig.autofmt_xdate()
        fig.tight_layout()
        filename = Path(output_dir) / "{}_{}.svg".format(*base_quote)
        plt.savefig(filename)
        plt.close(fig)

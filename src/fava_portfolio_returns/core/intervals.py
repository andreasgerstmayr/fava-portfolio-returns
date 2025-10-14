import datetime
from typing import Literal
from typing import NamedTuple

from dateutil.relativedelta import relativedelta

from fava_portfolio_returns._vendor.beangrow.reports import Interval

ONE_DAY = datetime.timedelta(days=1)


def intervals_heatmap(start_date: datetime.date, end_date: datetime.date) -> list[Interval]:
    """return all yearly and monthly intervals between start_date and end_date, clipped by end_date"""
    intervals = []
    for year in range(start_date.year, end_date.year + 1):
        intervals.append((f"{year}", datetime.date(year, 1, 1), min(end_date, datetime.date(year, 12, 31))))
        for month in range(1, 13):
            month_start = datetime.date(year, month, 1)
            month_end = (datetime.date(year, month + 1, 1) if month < 12 else datetime.date(year + 1, 1, 1)) - ONE_DAY
            if month_start <= end_date <= month_end:
                month_end = end_date
            intervals.append((f"{year}-{month:02}", month_start, month_end))
    return intervals


def intervals_yearly(start_date: datetime.date, end_date: datetime.date) -> list[Interval]:
    intervals = [
        (str(year), datetime.date(year, 1, 1), datetime.date(year, 12, 31))
        for year in range(start_date.year, end_date.year)
    ]
    intervals.append((str(end_date.year), datetime.date(end_date.year, 1, 1), end_date))
    return intervals


def intervals_periods(start_date: datetime.date, end_date: datetime.date) -> list[Interval]:
    periods = [
        ("3M", end_date - relativedelta(months=3), end_date),
        ("6M", end_date - relativedelta(months=6), end_date),
        ("YTD", datetime.date(end_date.year, 1, 1), end_date),
        ("1Y", datetime.date(end_date.year - 1, 1, 1), end_date),
        ("2Y", datetime.date(end_date.year - 2, 1, 1), end_date),
        ("3Y", datetime.date(end_date.year - 3, 1, 1), end_date),
        ("4Y", datetime.date(end_date.year - 4, 1, 1), end_date),
        ("5Y", datetime.date(end_date.year - 5, 1, 1), end_date),
        ("10Y", datetime.date(end_date.year - 10, 1, 1), end_date),
        ("15Y", datetime.date(end_date.year - 15, 1, 1), end_date),
        ("MAX", start_date, end_date),
    ]
    return [(label, start, end) for (label, start, end) in periods if start >= start_date]


class MonthInterval(NamedTuple):
    year: int
    month: int


def iterate_months(start_date: datetime.date, end_date: datetime.date) -> list[MonthInterval]:
    """iterate through months"""
    year = start_date.year
    month = start_date.month
    last_year = end_date.year
    last_month = end_date.month

    months = []
    while year < last_year or (year == last_year and month <= last_month):
        months.append(MonthInterval(year=year, month=month))
        if month == 12:
            year += 1
            month = 1
        else:
            month += 1
    return months


def iterate_years(start_date: datetime.date, end_date: datetime.date) -> list[int]:
    """iterate through years"""
    year = start_date.year
    last_year = end_date.year
    return list(range(year, last_year + 1))


def interval_label(interval: Literal["monthly", "yearly"]):
    if interval == "monthly":
        return lambda x: f"{x.year}-{x.month:02}"
    elif interval == "yearly":
        return lambda x: f"{x.year}"
    else:
        raise ValueError(f"Invalid interval {interval}")


def interval_labels(interval: Literal["monthly", "yearly"], start_date: datetime.date, end_date: datetime.date):
    if interval == "monthly":
        return [f"{m.year}-{m.month:02}" for m in iterate_months(start_date, end_date)]
    elif interval == "yearly":
        return [f"{year}" for year in iterate_years(start_date, end_date)]
    else:
        raise ValueError(f"Invalid interval {interval}")

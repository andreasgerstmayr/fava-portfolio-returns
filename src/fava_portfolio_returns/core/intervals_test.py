import datetime
import unittest

from fava_portfolio_returns.core.intervals import intervals_heatmap
from fava_portfolio_returns.core.intervals import intervals_periods
from fava_portfolio_returns.core.intervals import intervals_yearly


class TestIntervals(unittest.TestCase):
    def test_intervals_heatmap_single_year(self):
        start_date = datetime.date(2023, 3, 15)
        end_date = datetime.date(2023, 11, 20)
        intervals = intervals_heatmap(start_date, end_date)

        assert intervals == [
            ("2023", datetime.date(2023, 1, 1), datetime.date(2023, 11, 20)),
            ("2023-01", datetime.date(2023, 1, 1), datetime.date(2023, 1, 31)),
            ("2023-02", datetime.date(2023, 2, 1), datetime.date(2023, 2, 28)),
            ("2023-03", datetime.date(2023, 3, 1), datetime.date(2023, 3, 31)),
            ("2023-04", datetime.date(2023, 4, 1), datetime.date(2023, 4, 30)),
            ("2023-05", datetime.date(2023, 5, 1), datetime.date(2023, 5, 31)),
            ("2023-06", datetime.date(2023, 6, 1), datetime.date(2023, 6, 30)),
            ("2023-07", datetime.date(2023, 7, 1), datetime.date(2023, 7, 31)),
            ("2023-08", datetime.date(2023, 8, 1), datetime.date(2023, 8, 31)),
            ("2023-09", datetime.date(2023, 9, 1), datetime.date(2023, 9, 30)),
            ("2023-10", datetime.date(2023, 10, 1), datetime.date(2023, 10, 31)),
            ("2023-11", datetime.date(2023, 11, 1), datetime.date(2023, 11, 20)),
            ("2023-12", datetime.date(2023, 12, 1), datetime.date(2023, 12, 31)),
        ]

    def test_intervals_heatmap_multiple_years(self):
        start_date = datetime.date(2022, 10, 1)
        end_date = datetime.date(2024, 2, 15)
        intervals = intervals_heatmap(start_date, end_date)

        assert len(intervals) == 3 + 3 * 12

        year_intervals = [i for i in intervals if "-" not in i[0]]
        assert len(year_intervals) == 3
        assert year_intervals[0] == ("2022", datetime.date(2022, 1, 1), datetime.date(2022, 12, 31))
        assert year_intervals[1] == ("2023", datetime.date(2023, 1, 1), datetime.date(2023, 12, 31))
        assert year_intervals[2] == ("2024", datetime.date(2024, 1, 1), datetime.date(2024, 2, 15))

        feb_2024 = [i for i in intervals if i[0] == "2024-02"][0]
        assert feb_2024 == ("2024-02", datetime.date(2024, 2, 1), datetime.date(2024, 2, 15))

    def test_intervals_yearly_single_year(self):
        start_date = datetime.date(2023, 3, 15)
        end_date = datetime.date(2023, 11, 20)
        intervals = intervals_yearly(start_date, end_date)

        assert intervals == [("2023", datetime.date(2023, 1, 1), datetime.date(2023, 11, 20))]

    def test_intervals_yearly_multiple_years(self):
        start_date = datetime.date(2021, 3, 15)
        end_date = datetime.date(2023, 11, 20)
        intervals = intervals_yearly(start_date, end_date)

        assert intervals == [
            ("2021", datetime.date(2021, 1, 1), datetime.date(2021, 12, 31)),
            ("2022", datetime.date(2022, 1, 1), datetime.date(2022, 12, 31)),
            ("2023", datetime.date(2023, 1, 1), datetime.date(2023, 11, 20)),
        ]

    def test_intervals_periods(self):
        start_date = datetime.date(2020, 1, 1)
        end_date = datetime.date(2023, 6, 15)
        intervals = intervals_periods(start_date, end_date)

        assert intervals == [
            ("3M", datetime.date(2023, 3, 15), datetime.date(2023, 6, 15)),
            ("6M", datetime.date(2022, 12, 15), datetime.date(2023, 6, 15)),
            ("YTD", datetime.date(2023, 1, 1), datetime.date(2023, 6, 15)),
            ("1Y", datetime.date(2022, 1, 1), datetime.date(2023, 6, 15)),
            ("2Y", datetime.date(2021, 1, 1), datetime.date(2023, 6, 15)),
            ("3Y", datetime.date(2020, 1, 1), datetime.date(2023, 6, 15)),
            ("MAX", datetime.date(2020, 1, 1), datetime.date(2023, 6, 15)),
        ]

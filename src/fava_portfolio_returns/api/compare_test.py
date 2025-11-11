import datetime
import unittest

from fava_portfolio_returns.api.compare import NamedSeries
from fava_portfolio_returns.api.compare import compare_chart
from fava_portfolio_returns.test.test import approx2
from fava_portfolio_returns.test.test import load_portfolio_file


class TestCompare(unittest.TestCase):
    def test_savings_plan_simple(self):
        p = load_portfolio_file("savings_plan")
        series = compare_chart(p, datetime.date(2020, 1, 1), datetime.date(2020, 4, 1), "simple", ["c:CORP"])
        assert series == [
            NamedSeries(
                name="Returns",
                data=[
                    (datetime.date(2020, 1, 1), 0.0),
                    (datetime.date(2020, 2, 1), 0.2),
                    (datetime.date(2020, 3, 1), approx2(0.33)),
                    (datetime.date(2020, 4, 1), approx2(0.43)),
                ],
            ),
            NamedSeries(
                name="CORP (CORP)",
                data=[
                    (datetime.date(2020, 1, 1), 0.0),
                    (datetime.date(2020, 2, 1), 0.5),
                    (datetime.date(2020, 3, 1), 1),
                    (datetime.date(2020, 4, 1), 1.5),
                ],
            ),
        ]

    def test_savings_plan_twr(self):
        p = load_portfolio_file("savings_plan")
        series = compare_chart(p, datetime.date(2020, 1, 1), datetime.date(2020, 4, 1), "twr", ["c:CORP"])
        assert series == [
            NamedSeries(
                name="Returns",
                data=[
                    # TWR is identical to price series, because effects of cash flows are eliminated
                    (datetime.date(2020, 1, 1), 0.0),
                    (datetime.date(2020, 2, 1), 0.5),
                    (datetime.date(2020, 3, 1), 1.0),
                    (datetime.date(2020, 4, 1), 1.5),
                ],
            ),
            NamedSeries(
                name="CORP (CORP)",
                data=[
                    (datetime.date(2020, 1, 1), 0.0),
                    (datetime.date(2020, 2, 1), 0.5),
                    (datetime.date(2020, 3, 1), 1.0),
                    (datetime.date(2020, 4, 1), 1.5),
                ],
            ),
        ]

    def test_savings_plan_middle(self):
        p = load_portfolio_file("savings_plan")
        series = compare_chart(p, datetime.date(2020, 3, 1), datetime.date(2020, 4, 1), "simple", ["c:CORP"])
        assert series == [
            NamedSeries(
                name="Returns",
                data=[
                    (datetime.date(2020, 3, 1), 0.0),
                    (datetime.date(2020, 4, 1), approx2(0.09)),
                ],
            ),
            NamedSeries(
                name="CORP (CORP)",
                data=[
                    (datetime.date(2020, 3, 1), 0.0),
                    (datetime.date(2020, 4, 1), 0.25),
                ],
            ),
        ]

    def test_linear_growth_stock_simple(self):
        p = load_portfolio_file("linear_growth_stock")
        series = compare_chart(p, datetime.date(2020, 1, 1), datetime.date(2020, 6, 1), "simple", ["c:CORP"])
        assert series == [
            NamedSeries(
                name="Returns",
                data=[
                    (datetime.date(2020, 1, 1), 0.0),
                    (datetime.date(2020, 2, 1), 0.5),
                    (datetime.date(2020, 3, 1), 1.0),
                    (datetime.date(2020, 4, 1), approx2(0.42)),  # returns dropped because of investment
                    (datetime.date(2020, 5, 1), approx2(0.71)),
                    (datetime.date(2020, 6, 1), 1.0),
                ],
            ),
            NamedSeries(
                name="CORP (CORP)",
                data=[
                    (datetime.date(2020, 1, 1), 0.0),
                    (datetime.date(2020, 2, 1), 0.5),
                    (datetime.date(2020, 3, 1), 1.0),
                    (datetime.date(2020, 4, 1), 1.5),
                    (datetime.date(2020, 5, 1), 2.0),
                    (datetime.date(2020, 6, 1), 2.5),
                ],
            ),
        ]

    def test_linear_growth_stock_twr(self):
        p = load_portfolio_file("linear_growth_stock")
        series = compare_chart(p, datetime.date(2020, 1, 1), datetime.date(2020, 6, 1), "twr", ["c:CORP"])
        assert series == [
            NamedSeries(
                name="Returns",
                data=[
                    # TWR is identical to price series, because effects of cash flows are eliminated
                    (datetime.date(2020, 1, 1), 0.0),
                    (datetime.date(2020, 2, 1), 0.5),
                    (datetime.date(2020, 3, 1), 1.0),
                    (datetime.date(2020, 4, 1), 1.5),
                    (datetime.date(2020, 5, 1), 2.0),
                    (datetime.date(2020, 6, 1), 2.5),
                ],
            ),
            NamedSeries(
                name="CORP (CORP)",
                data=[
                    (datetime.date(2020, 1, 1), 0.0),
                    (datetime.date(2020, 2, 1), 0.5),
                    (datetime.date(2020, 3, 1), 1.0),
                    (datetime.date(2020, 4, 1), 1.5),
                    (datetime.date(2020, 5, 1), 2.0),
                    (datetime.date(2020, 6, 1), 2.5),
                ],
            ),
        ]

    def test_portfolio_common_date_doesnt_change_twr(self):
        # test to prevent wrong TWR calculation if some dates in the beginning of the series have to be omitted
        # (if the common date is later than the first date)
        p = load_portfolio_file("portfolio_vs_currency", investment_filter=["c:CORP1"])
        # common date is 2020-02-05 since CORP2 doesn't have earlier pricing or transactions
        # presence of c:CORP2 in the filter changes the starting date from 2020-02-01 to 2020-02-05
        series = compare_chart(p, datetime.date(2020, 1, 1), datetime.date(2020, 3, 15), "twr", ["c:CORP1", "c:CORP2"])
        # Note that TWR Returns of the portfolio and stock price should be identical because there were no fees or
        # any other cash flows that would create the difference
        assert series == [
            NamedSeries(
                name="Returns",
                data=[
                    (datetime.date(2020, 2, 5), 0.0),
                    (datetime.date(2020, 2, 10), 0.25),
                    (datetime.date(2020, 3, 1), approx2(0.67)),
                ],
            ),
            NamedSeries(
                name="CORP1 (CORP1)",
                data=[
                    (datetime.date(2020, 2, 5), 0.0),
                    (datetime.date(2020, 2, 10), 0.25),
                    (datetime.date(2020, 3, 1), approx2(0.67)),
                ],
            ),
            NamedSeries(
                name="CORP2 (CORP2)",
                data=[
                    (datetime.date(2020, 2, 5), 0.0),
                    (datetime.date(2020, 3, 10), 0.5),
                ],
            ),
        ]

import { Alert } from "@mui/material";
import { usePortfolio } from "../api/portfolio";
import { Dashboard, DashboardRow, Panel, PanelGroup } from "../components/Dashboard";
import { EChart } from "../components/EChart";
import { useToolbarContext } from "../components/Header/ToolbarProvider";
import { Loading } from "../components/Loading";
import {
  getCurrencyFormatter,
  getIntegerCurrencyFormatter,
  NEGATIVE_NUMBER_COLOR,
  NEGATIVE_TREND_COLOR,
  POSITIVE_NUMBER_COLOR,
  POSITIVE_TREND_COLOR,
  timestampToDate,
} from "../components/format";

export function Portfolio() {
  return (
    <Dashboard>
      <DashboardRow>
        <PanelGroup param="chart" labels={["Performance", "Portfolio Value"]}>
          <Panel
            title="Performance"
            help="The performance chart shows the gain or loss of the portfolio."
            sx={{ flex: 2 }}
          >
            <PerformanceChart />
          </Panel>
          <Panel
            title="Portfolio Value"
            help="The portfolio value chart compares the portfolio value with the invested capital, including dividends and fees."
            sx={{ flex: 2 }}
          >
            <PortfolioValueChart />
          </Panel>
        </PanelGroup>
        <Panel title="Allocation">
          <AllocationChart />
        </Panel>
      </DashboardRow>
    </Dashboard>
  );
}

function PerformanceChart() {
  const { investmentFilter, targetCurrency } = useToolbarContext();
  const { isPending, error, data } = usePortfolio({
    investmentFilter,
    targetCurrency,
  });

  if (isPending) {
    return <Loading />;
  }
  if (error) {
    return <Alert severity="error">{error.message}</Alert>;
  }

  const series = data.performance;
  const firstValue = series.length > 0 ? series[0][1] : 0;
  const lastValue = series.length > 0 ? series[series.length - 1][1] : 0;
  const trendColor = lastValue >= firstValue ? POSITIVE_TREND_COLOR : NEGATIVE_TREND_COLOR;
  const currencyFormatter = getCurrencyFormatter(targetCurrency);
  const option = {
    tooltip: {
      trigger: "axis",
      valueFormatter: currencyFormatter,
    },
    grid: {
      left: 100,
      right: 20,
    },
    xAxis: {
      type: "time",
      axisPointer: {
        label: {
          formatter: ({ value }: { value: number }) => timestampToDate(value),
        },
      },
    },
    yAxis: {
      type: "value",
      axisLabel: {
        formatter: currencyFormatter,
      },
    },
    series: {
      type: "line",
      name: "Performance",
      showSymbol: false,
      data: series,
      lineStyle: {
        color: trendColor(),
      },
      itemStyle: {
        color: trendColor(),
      },
      areaStyle: {
        color: {
          type: "linear",
          x: 0,
          y: 0,
          x2: 0,
          y2: 1,
          colorStops: [
            {
              offset: 0,
              color: trendColor(0.2),
            },
            {
              offset: 1,
              color: trendColor(0),
            },
          ],
        },
      },
    },
  };

  return <EChart height="400px" option={option} />;
}

function PortfolioValueChart() {
  const { investmentFilter, targetCurrency } = useToolbarContext();
  const { isPending, error, data } = usePortfolio({
    investmentFilter,
    targetCurrency,
  });

  if (isPending) {
    return <Loading />;
  }
  if (error) {
    return <Alert severity="error">{error.message}</Alert>;
  }

  const currencyFormatter = getCurrencyFormatter(targetCurrency);
  const option = {
    tooltip: {
      trigger: "axis",
      formatter: (params: { value: { date: string; market: number; cash: number }; marker: string }[]) => {
        function marker(color: string) {
          return `<span style="display:inline-block;margin-right:4px;border-radius:10px;width:10px;height:10px;background-color:${color};"></span>`;
        }
        function valueFmt(value: number, style?: string) {
          return `<span style="float: right; margin-left:15px; font-weight: bold; ${style ?? ""}">${currencyFormatter(value)}</span>`;
        }

        // note: array order matches 'series' option order!
        const [valueSeries, capitalSeries] = params;
        const value = valueSeries.value;
        const difference = value.market - value.cash;
        const diffColor = difference >= 0 ? POSITIVE_NUMBER_COLOR : NEGATIVE_NUMBER_COLOR;

        return (
          `${value.date}<br>` +
          `${valueSeries.marker} Portfolio Value ${valueFmt(value.market)}<br>` +
          `${capitalSeries.marker} Invested Capital ${valueFmt(value.cash)}<br>` +
          `${marker("#ccc")} Difference ${valueFmt(difference, `color: ${diffColor}`)}`
        );
      },
    },
    legend: {
      bottom: 0,
    },
    grid: {
      left: 100,
      right: 20,
    },
    xAxis: {
      type: "time",
    },
    yAxis: {
      type: "value",
      axisLabel: {
        formatter: currencyFormatter,
      },
    },
    dataset: {
      source: data.chart,
    },
    series: [
      {
        type: "line",
        name: "Portfolio Value",
        showSymbol: false,
        dimensions: ["date", "market"],
      },
      {
        type: "line",
        name: "Invested Capital",
        showSymbol: false,
        dimensions: ["date", "cash"],
        step: "end", // increase invested capital at date of cash flow, do not interpolate
        lineStyle: {
          type: "dotted",
        },
      },
    ],
  };

  return <EChart height="400px" option={option} />;
}

function AllocationChart() {
  const { investmentFilter, setInvestmentFilter, targetCurrency } = useToolbarContext();
  const { isPending, error, data } = usePortfolio({ investmentFilter, targetCurrency });

  if (isPending) {
    return <Loading />;
  }
  if (error) {
    return <Alert severity="error">{error.message}</Alert>;
  }

  const currencyFormatter = getIntegerCurrencyFormatter(targetCurrency);
  const option = {
    series: [
      {
        type: "pie",
        radius: ["60%", "90%"],
        avoidLabelOverlap: false,
        padAngle: 1,
        itemStyle: {
          borderRadius: 3,
        },
        label: {
          show: false,
          position: "center",
          formatter: (params: { data: { name: string; value: number } }) => {
            return `{name|${params.data.name}}\n{value|${currencyFormatter(params.data.value)}}`;
          },

          rich: {
            name: {
              fontSize: 16,
            },
            value: {
              fontSize: 20,
              fontWeight: "bold",
            },
          },
        },
        emphasis: {
          label: {
            show: true,
          },
        },
        labelLine: {
          show: false,
        },
        data: data.allocation.map((i) => ({ name: i.name, currency: i.currency, value: i.marketValue })),
      },
    ],
    onClick: (params: { data: { currency: string } }) => {
      setInvestmentFilter([`c:${params.data.currency}`]);
    },
  };

  // compensate for empty help text
  return (
    <>
      <p>&nbsp;</p>
      <EChart height="400px" option={option} />
    </>
  );
}

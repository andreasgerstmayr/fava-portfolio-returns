import { Alert, useTheme } from "@mui/material";
import { usePortfolio } from "../api/portfolio";
import { Dashboard, DashboardRow, Panel, PanelGroup } from "../components/Dashboard";
import { EChart } from "../components/EChart";
import { useToolbarContext } from "../components/Header/ToolbarProvider";
import { Loading } from "../components/Loading";
import { getCurrencyFormatter, getIntegerCurrencyFormatter, timestampToDate } from "../components/format";

export function Portfolio() {
  return (
    <Dashboard>
      <DashboardRow>
        <PanelGroup param="chart" labels={["Performance", "Portfolio Value"]}>
          <Panel
            title="Performance"
            help="The performance chart shows the total profit and loss of the portfolio."
            sx={{ flex: 2 }}
          >
            <PerformanceChart />
          </Panel>
          <Panel
            title="Portfolio Value"
            help="The portfolio value chart compares the market value with the cost value of the portfolio."
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
  const theme = useTheme();
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

  const series = data.performanceChart;
  const firstValue = series.length > 0 ? series[0][1] : 0;
  const lastValue = series.length > 0 ? series[series.length - 1][1] : 0;
  const trendColor = lastValue >= firstValue ? theme.trend.positive : theme.trend.negative;
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
      name: "Total P/L",
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
      valueFormatter: currencyFormatter,
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
    dataset: {
      source: data.valueChart,
    },
    series: [
      {
        type: "line",
        name: "Market Value",
        showSymbol: false,
        dimensions: ["date", "market"],
      },
      {
        type: "line",
        name: "Cost Value",
        showSymbol: false,
        dimensions: ["date", "cost"],
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

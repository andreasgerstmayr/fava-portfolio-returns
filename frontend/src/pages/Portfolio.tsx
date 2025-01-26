import { Alert } from "@mui/material";
import { useAllocation } from "../api/allocation";
import { useSeries } from "../api/series";
import { useSummary } from "../api/summary";
import { Dashboard, DashboardRow, Panel, PanelGroup } from "../components/Dashboard";
import { EChart } from "../components/EChart";
import { useToolbarContext } from "../components/Header/ToolbarProvider";
import { Loading } from "../components/Loading";
import {
  NEGATIVE_NUMBER_COLOR,
  NEGATIVE_TREND_COLOR,
  POSITIVE_NUMBER_COLOR,
  POSITIVE_TREND_COLOR,
} from "../components/style";

export function Portfolio() {
  return (
    <Dashboard>
      <DashboardRow>
        <PanelGroup labels={["Performance", "Portfolio Value"]}>
          <Panel
            title="Performance"
            help="The performance chart shows the profit and loss of the portfolio."
            sx={{ flex: 2 }}
          >
            <PerformanceChart />
          </Panel>
          <Panel
            title="Portfolio Value"
            help="The portfolio value chart compares the invested capital with the portfolio value."
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
  const { isPending, error, data } = useSeries({
    investmentFilter,
    targetCurrency,
    series: ["portfolio_returns"],
  });

  if (isPending) {
    return <Loading />;
  }
  if (error) {
    return <Alert severity="error">{error.message}</Alert>;
  }

  const currencyFormatter = new Intl.NumberFormat(undefined, {
    style: "currency",
    currency: targetCurrency,
  }).format;
  const signedCurrencyFormatter = new Intl.NumberFormat(undefined, {
    style: "currency",
    currency: targetCurrency,
    signDisplay: "exceptZero",
  }).format;

  const series = data.series["portfolio_returns"];
  const firstValue = series.length > 0 ? series[0][1] : 0;
  const lastValue = series.length > 0 ? series[series.length - 1][1] : 0;
  const color = lastValue >= firstValue ? POSITIVE_TREND_COLOR : NEGATIVE_TREND_COLOR;

  const option = {
    tooltip: {
      trigger: "axis",
      valueFormatter: signedCurrencyFormatter,
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
    series: {
      type: "line",
      name: "Performance",
      showSymbol: false,
      data: series,
      lineStyle: {
        color: color(),
      },
      itemStyle: {
        color: color(),
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
              color: color(0.2),
            },
            {
              offset: 1,
              color: color(0),
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
  const { isPending, error, data } = useSeries({
    investmentFilter,
    targetCurrency,
    series: ["portfolio_market_values", "cash_flows_cumulative"],
  });

  if (isPending) {
    return <Loading />;
  }
  if (error) {
    return <Alert severity="error">{error.message}</Alert>;
  }

  const currencyFormatter = new Intl.NumberFormat(undefined, {
    style: "currency",
    currency: targetCurrency,
  }).format;

  const marketValues = data.series["portfolio_market_values"];
  const cashFlowsValues = data.series["cash_flows_cumulative"];

  const option = {
    tooltip: {
      trigger: "axis",
      formatter: (chart: echarts.ECharts, params: { value: string[] }[]) => {
        const axisDate = params[0].value[0];

        function findSeriesValue(series: [string, number][]) {
          let i = -1;
          while (i + 1 < series.length && series[i + 1][0] <= axisDate) {
            i++;
          }
          return i >= 0 ? series[i][1] : undefined;
        }
        function marker(color: string) {
          return `<span style="display:inline-block;margin-right:4px;border-radius:10px;width:10px;height:10px;background-color:${color};"></span>`;
        }
        function valueFmt(value: number | undefined, style?: string) {
          return `<span style="float: right; margin-left:15px; font-weight: bold; ${style || ""}">${value === undefined ? "" : currencyFormatter(value)}</span>`;
        }

        const marketValue = findSeriesValue(marketValues);
        const cashFlowsValue = findSeriesValue(cashFlowsValues);
        const difference =
          marketValue !== undefined && cashFlowsValue !== undefined ? marketValue - cashFlowsValue : undefined;
        const diffColor = difference === undefined || difference >= 0 ? POSITIVE_NUMBER_COLOR : NEGATIVE_NUMBER_COLOR;

        // note: sync seriesIndex and description with series option!
        return (
          `${axisDate}<br>` +
          `${marker(chart.getVisual({ seriesIndex: 0 }, "color") as string)} Portfolio Value ${valueFmt(marketValue)}<br>` +
          `${marker(chart.getVisual({ seriesIndex: 1 }, "color") as string)} Invested Capital ${valueFmt(cashFlowsValue)}<br>` +
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
    series: [
      {
        type: "line",
        name: "Portfolio Value",
        showSymbol: false,
        data: marketValues,
      },
      {
        type: "line",
        name: "Invested Capital",
        showSymbol: false,
        step: "end", // increase invested capital at date of cash flow, do not interpolate
        data: cashFlowsValues,
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
  const { isPending, error, data } = useAllocation({ investmentFilter, targetCurrency });

  if (isPending) {
    return <Loading />;
  }
  if (error) {
    return <Alert severity="error">{error.message}</Alert>;
  }

  const currencyFormatter = new Intl.NumberFormat(undefined, {
    style: "currency",
    currency: targetCurrency,
    maximumFractionDigits: 0,
  }).format;

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
        data: data.allocation.map((i) => ({ name: i.commodity, currency: i.currency, value: i.marketValue })),
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

// eslint-disable-next-line @typescript-eslint/no-unused-vars
function SummaryTable() {
  const { investmentFilter, targetCurrency } = useToolbarContext();
  const { isPending, error, data } = useSummary({ investmentFilter, targetCurrency });

  if (isPending) {
    return <Loading />;
  }
  if (error) {
    return <Alert severity="error">{error.message}</Alert>;
  }

  const currencyFormatter = new Intl.NumberFormat(undefined, {
    style: "currency",
    currency: targetCurrency,
  }).format;

  const percentFormatter = new Intl.NumberFormat(undefined, {
    style: "percent",
    maximumFractionDigits: 2,
  }).format;

  const summary = data.summary;

  return (
    <table>
      <thead>
        <tr>
          <th>Name</th>
          <th>Value</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td>Market Value</td>
          <td className="num">{currencyFormatter(summary.marketValue)}</td>
        </tr>
        <tr>
          <td>Cash In</td>
          <td className="num">{currencyFormatter(summary.cashIn)}</td>
        </tr>
        <tr>
          <td>Cash Out</td>
          <td className="num">{currencyFormatter(summary.cashOut)}</td>
        </tr>
        <tr>
          <td title="Market Value + Cash Out - Cash In">Returns</td>
          <td className="num" style={{ color: summary.returns >= 0 ? POSITIVE_NUMBER_COLOR : NEGATIVE_NUMBER_COLOR }}>
            {currencyFormatter(summary.returns)}
          </td>
        </tr>
        <tr>
          <td title="(Market Value - Invested Capital) / Invested Capital">Returns pct</td>
          <td
            className="num"
            style={{ color: summary.returnsPct >= 0 ? POSITIVE_NUMBER_COLOR : NEGATIVE_NUMBER_COLOR }}
          >
            {percentFormatter(summary.returnsPct)}
            <br />
            p.a. {percentFormatter(summary.returnsPctAnnualized)}
          </td>
        </tr>
        <tr>
          <td>IRR</td>
          <td className="num" style={{ color: summary.irr >= 0 ? POSITIVE_NUMBER_COLOR : NEGATIVE_NUMBER_COLOR }}>
            {percentFormatter(summary.irr)}
          </td>
        </tr>
        <tr>
          <td>TWR</td>
          <td className="num" style={{ color: summary.twr >= 0 ? POSITIVE_NUMBER_COLOR : NEGATIVE_NUMBER_COLOR }}>
            {percentFormatter(summary.twr)}
          </td>
        </tr>
      </tbody>
    </table>
  );
}

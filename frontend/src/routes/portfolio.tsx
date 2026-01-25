import { Alert, useTheme } from "@mui/material";
import { createRoute, stripSearchParams } from "@tanstack/react-router";
import { ECElementEvent, EChartsOption } from "echarts";
import { useTranslation } from "react-i18next";
import { z } from "zod";
import { usePortfolio } from "../api/portfolio";
import { Dashboard, DashboardRow, Panel, PanelGroup, PanelGroupItem } from "../components/Dashboard";
import { EChart, EChartsSpec } from "../components/EChart";
import { useToolbarContext } from "../components/Header/ToolbarProvider";
import { Loading } from "../components/Loading";
import { anyFormatter, timestampToDate, useCurrencyFormatter } from "../components/format";
import { useSearchParam } from "../components/useSearchParam";
import { RootRoute } from "./__root";

const searchSchema = z.object({
  chart: z.enum(["performance", "value"]).default("performance").catch("performance"),
});

export const PortfolioRoute = createRoute({
  getParentRoute: () => RootRoute,
  path: "portfolio",
  validateSearch: searchSchema,
  search: {
    middlewares: [stripSearchParams({ chart: "performance" })],
  },
  component: Portfolio,
});

function Portfolio() {
  const { t } = useTranslation();
  const [chart, setChart] = useSearchParam(PortfolioRoute, "chart");

  return (
    <Dashboard>
      <DashboardRow>
        <PanelGroup active={chart} setActive={setChart}>
          <PanelGroupItem id="performance" label={t("Performance")}>
            <Panel
              title={t("Performance")}
              help={t("The performance chart shows the total profit and loss of the portfolio.")}
              sx={{ flex: 2 }}
            >
              <PerformanceChart />
            </Panel>
          </PanelGroupItem>
          <PanelGroupItem id="value" label={t("Portfolio Value")}>
            <Panel
              title={t("Portfolio Value")}
              help={t("The portfolio value chart compares the market value with the cost value of the portfolio.")}
              sx={{ flex: 2 }}
            >
              <PortfolioValueChart />
            </Panel>
          </PanelGroupItem>
        </PanelGroup>
        <Panel title={t("Allocation")}>
          <AllocationChart />
        </Panel>
      </DashboardRow>
    </Dashboard>
  );
}

function PerformanceChart() {
  const { t } = useTranslation();
  const theme = useTheme();
  const { investmentFilter, targetCurrency } = useToolbarContext();
  const currencyFormatter = useCurrencyFormatter(targetCurrency);
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
  const option: EChartsOption = {
    tooltip: {
      trigger: "axis",
      valueFormatter: anyFormatter(currencyFormatter),
    },
    grid: {
      left: 100,
      right: 20,
    },
    xAxis: {
      type: "time",
      axisPointer: {
        label: {
          formatter: (params) => timestampToDate(params.value as number),
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
      name: t("Total P/L"),
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
  const { t } = useTranslation();
  const { investmentFilter, targetCurrency } = useToolbarContext();
  const currencyFormatter = useCurrencyFormatter(targetCurrency);
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

  const option: EChartsOption = {
    tooltip: {
      trigger: "axis",
      valueFormatter: anyFormatter(currencyFormatter),
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
          formatter: (params) => timestampToDate(params.value as number),
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
        name: t("Market Value"),
        showSymbol: false,
        encode: { x: "date", y: "market" },
      },
      {
        type: "line",
        name: t("Cost Value"),
        showSymbol: false,
        encode: { x: "date", y: "cost" },
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
  const currencyFormatter = useCurrencyFormatter(targetCurrency, { integer: true });
  const { isPending, error, data } = usePortfolio({ investmentFilter, targetCurrency });

  if (isPending) {
    return <Loading />;
  }
  if (error) {
    return <Alert severity="error">{error.message}</Alert>;
  }

  const option: EChartsSpec = {
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
          formatter: (params) => {
            const data = params.data as { name: string; value: number };
            return `{name|${data.name}}\n{value|${currencyFormatter(data.value)}}`;
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
    onClick: (params: ECElementEvent) => {
      const data = params.data as { currency: string };
      setInvestmentFilter([`c_${data.currency}`]);
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

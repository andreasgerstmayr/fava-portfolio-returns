import { Alert, useTheme } from "@mui/material";
import { createRoute, stripSearchParams } from "@tanstack/react-router";
import { EChartsOption } from "echarts";
import { useTranslation } from "react-i18next";
import { z } from "zod";
import { useMetricValues } from "../api/metric_values";
import { Dashboard, DashboardRow, Panel } from "../components/Dashboard";
import { EChart } from "../components/EChart";
import { useToolbarContext } from "../components/Header/ToolbarProvider";
import { Loading } from "../components/Loading";
import { MetricName, MetricSelection, useMetric } from "../components/MetricSelection";
import { anyFormatter, useCurrencyFormatter, usePercentFormatter } from "../components/format";
import { useSearchParam } from "../components/useSearchParam";
import { RootRoute } from "./__root";

const supportedMetrics: MetricName[] = ["volatility", "mdd"];
const searchSchema = z.object({
  metric: z.enum(supportedMetrics).default("volatility").catch("volatility"),
});

export const MetricsRoute = createRoute({
  getParentRoute: () => RootRoute,
  path: "metrics",
  validateSearch: searchSchema,
  search: {
    middlewares: [stripSearchParams({ metric: "volatility" })],
  },
  component: Metrics,
});

function Metrics() {
  const { t } = useTranslation();
  const [metric, setMetric] = useSearchParam(MetricsRoute, "metric");
  const metricDef = useMetric(metric);
  const panelTitle = metricDef.supportSeries
    ? metricDef.label
    : t("{{metricName}} (rolling 1y)", { metricName: metricDef.label });

  return (
    <Dashboard>
      <DashboardRow sx={{ justifyContent: "flex-end" }}>
        <MetricSelection options={supportedMetrics} value={metric} setValue={setMetric} />
      </DashboardRow>
      <DashboardRow>
        <Panel title={panelTitle}>
          <MetricLineChart metric={metric} />
        </Panel>
      </DashboardRow>
      <DashboardRow>
        <Panel title={t("Monthly Heatmap")}>
          <MetricHeatmapChart metric={metric} />
        </Panel>
      </DashboardRow>
      <DashboardRow>
        <Panel title={t("Years")}>
          <MetricBarChart metric={metric} interval="yearly" />
        </Panel>
        <Panel title={t("Periods")}>
          <MetricBarChart metric={metric} interval="periods" />
        </Panel>
      </DashboardRow>
    </Dashboard>
  );
}

interface MetricLineChartProps {
  metric: MetricName;
}

export function MetricLineChart({ metric }: MetricLineChartProps) {
  const { investmentFilter, targetCurrency } = useToolbarContext();
  const metricDef = useMetric(metric);
  const currencyFormatter = useCurrencyFormatter(targetCurrency, { integer: true });
  const percentFormatter = usePercentFormatter();
  const valueFormatter = metricDef.unit === "currency" ? currencyFormatter : percentFormatter;
  const { isPending, error, data } = useMetricValues({
    investmentFilter,
    targetCurrency,
    metric,
    interval: metricDef.supportSeries ? "series" : "rolling_1y",
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
      valueFormatter: anyFormatter(valueFormatter),
    },
    grid: {
      left: 120,
      right: 100,
    },
    xAxis: {
      type: "time",
    },
    yAxis: {
      type: "value",
      axisLabel: {
        formatter: valueFormatter,
      },
    },
    series: {
      type: "line",
      name: metricDef.label,
      showSymbol: false,
      data: data.series,
    },
  };

  return <EChart height="400px" option={option} />;
}

interface MetricHeatmapChartProps {
  metric: MetricName;
}

export function MetricHeatmapChart({ metric }: MetricHeatmapChartProps) {
  const { t } = useTranslation();
  const theme = useTheme();
  const { investmentFilter, targetCurrency } = useToolbarContext();
  const metricDef = useMetric(metric);
  const currencyFormatter = useCurrencyFormatter(targetCurrency, { integer: true });
  const percentFormatter = usePercentFormatter();
  const valueFormatter = metricDef.unit === "currency" ? currencyFormatter : percentFormatter;
  const { isPending, error, data } = useMetricValues({
    investmentFilter,
    targetCurrency,
    metric,
    interval: "heatmap",
  });

  if (isPending) {
    return <Loading />;
  }
  if (error) {
    return <Alert severity="error">{error.message}</Alert>;
  }

  const max = Math.max(...data.series.map(([label, val]) => (label.includes("-") ? Math.abs(val) : 0)));
  const maxRounded = Math.round(max * 100) / 100;
  const monthFormatter = new Intl.DateTimeFormat(undefined, { month: "short" }).format;
  const option: EChartsOption = {
    tooltip: {
      position: "top",
      valueFormatter: anyFormatter(valueFormatter),
    },
    grid: {
      bottom: 100, // space for visualMap
    },
    xAxis: {
      type: "category",
    },
    yAxis: {
      type: "category",
    },
    visualMap: {
      min: -maxRounded,
      max: maxRounded,
      calculable: true, // show handles
      orient: "horizontal",
      left: "center",
      bottom: 0, // place visualMap at bottom of chart
      itemHeight: 400, // width
      inRange: {
        color: [theme.pnl.loss, "#fff", theme.pnl.profit],
      },
      formatter: anyFormatter(valueFormatter),
    },
    series: [
      {
        type: "heatmap",
        data: data.series.map(([label, value]) => {
          if (!label.includes("-")) {
            return [t("Entire Year"), label, value];
          }

          const [year, month] = label.split("-");
          const monthLocale = monthFormatter(new Date(parseInt(year), parseInt(month) - 1, 1));

          // workaround to display -0.0000001 as 0 instead of -0
          const valueRounded = Math.round((value + Number.EPSILON) * 10000) / 10000 + 0;
          return [monthLocale, year, valueRounded];
        }),
        label: {
          show: true,
          formatter: ({ data }) => valueFormatter((data as [string, string, number])[2]),
        },
        emphasis: {
          itemStyle: {
            shadowBlur: 10,
            shadowColor: "rgba(0, 0, 0, 0.5)",
          },
        },
      },
    ],
  };

  const numRows = data.series.filter(([label]) => !label.includes("-")).length;
  const chartHeightPx = 170 + numRows * 40;

  return <EChart height={`${chartHeightPx}px`} option={option} />;
}

interface MetricBarChartProps {
  metric: MetricName;
  interval: "yearly" | "periods";
}

export function MetricBarChart({ metric, interval }: MetricBarChartProps) {
  const { t } = useTranslation();
  const theme = useTheme();
  const { investmentFilter, targetCurrency } = useToolbarContext();
  const metricDef = useMetric(metric);
  const currencyFormatter = useCurrencyFormatter(targetCurrency, { integer: true });
  const percentFormatter = usePercentFormatter();
  const valueFormatter = metricDef.unit === "currency" ? currencyFormatter : percentFormatter;
  const { isPending, error, data } = useMetricValues({
    investmentFilter,
    targetCurrency,
    metric,
    interval,
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
      valueFormatter: anyFormatter(valueFormatter),
    },
    xAxis: {
      type: "category",
    },
    yAxis: {
      type: "value",
      axisLabel: {
        formatter: valueFormatter,
      },
    },
    series: [
      {
        type: "bar",
        name: t("Returns"),
        data: data.series,
        itemStyle: {
          color: (params) => {
            const data = params.data as [string, number];
            return data[1] >= 0 ? theme.pnl.profit : theme.pnl.loss;
          },
        },
      },
    ],
  };

  return <EChart height="400px" option={option} />;
}

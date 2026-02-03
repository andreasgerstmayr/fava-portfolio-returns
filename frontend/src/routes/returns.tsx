import { Alert, useTheme } from "@mui/material";
import { createRoute, stripSearchParams } from "@tanstack/react-router";
import { EChartsOption } from "echarts";
import { useTranslation } from "react-i18next";
import { z } from "zod";
import { useReturns } from "../api/returns";
import { Dashboard, DashboardRow, Panel } from "../components/Dashboard";
import { EChart } from "../components/EChart";
import { useToolbarContext } from "../components/Header/ToolbarProvider";
import { Loading } from "../components/Loading";
import { ReturnsMethod, ReturnsMethodSelection } from "../components/ReturnsMethodSelection";
import { anyFormatter, useCurrencyFormatter, usePercentFormatter } from "../components/format";
import { useSearchParam } from "../components/useSearchParam";
import { RootRoute } from "./__root";

const supportedMethods: ReturnsMethod[] = ["irr", "mdm", "twr", "pnl"];
const searchSchema = z.object({
  method: z.enum(supportedMethods).default("irr").catch("irr"),
});

export const ReturnsRoute = createRoute({
  getParentRoute: () => RootRoute,
  path: "returns",
  validateSearch: searchSchema,
  search: {
    middlewares: [stripSearchParams({ method: "irr" })],
  },
  component: Returns,
});

function Returns() {
  const { t } = useTranslation();
  const [method, setMethod] = useSearchParam(ReturnsRoute, "method");

  return (
    <Dashboard>
      <DashboardRow sx={{ justifyContent: "flex-end" }}>
        <ReturnsMethodSelection options={supportedMethods} method={method} setMethod={setMethod} />
      </DashboardRow>
      <DashboardRow>
        <Panel title={t("Monthly Returns")}>
          <ReturnsHeatmapChart method={method} />
        </Panel>
      </DashboardRow>
      <DashboardRow>
        <Panel title={t("Yearly Returns")}>
          <ReturnsBarChart method={method} interval="yearly" />
        </Panel>
        <Panel title={t("Returns over Periods")}>
          <ReturnsBarChart method={method} interval="periods" />
        </Panel>
      </DashboardRow>
    </Dashboard>
  );
}

interface ReturnsHeatmapChartProps {
  method: ReturnsMethod;
}

function ReturnsHeatmapChart({ method }: ReturnsHeatmapChartProps) {
  const { t } = useTranslation();
  const theme = useTheme();
  const { investmentFilter, targetCurrency } = useToolbarContext();
  const currencyFormatter = useCurrencyFormatter(targetCurrency, { integer: true });
  const percentFormatter = usePercentFormatter();
  const { isPending, error, data } = useReturns({
    investmentFilter,
    targetCurrency,
    method,
    interval: "heatmap",
  });

  if (isPending) {
    return <Loading />;
  }
  if (error) {
    return <Alert severity="error">{error.message}</Alert>;
  }

  const max = Math.max(...data.returns.map(([label, val]) => (label.includes("-") ? Math.abs(val) : 0)));
  const maxRounded = Math.round(max * 100) / 100;
  const valueFormatter = method === "pnl" ? currencyFormatter : percentFormatter;
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
        data: data.returns.map(([label, value]) => {
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

  const numRows = data.returns.filter(([label]) => !label.includes("-")).length;
  const chartHeightPx = 170 + numRows * 40;

  return <EChart height={`${chartHeightPx}px`} option={option} />;
}

interface ReturnsBarChartProps {
  method: ReturnsMethod;
  interval: "yearly" | "periods";
}

function ReturnsBarChart({ method, interval }: ReturnsBarChartProps) {
  const { t } = useTranslation();
  const theme = useTheme();
  const { investmentFilter, targetCurrency } = useToolbarContext();
  const currencyFormatter = useCurrencyFormatter(targetCurrency, { integer: true });
  const percentFormatter = usePercentFormatter();
  const { isPending, error, data } = useReturns({
    investmentFilter,
    targetCurrency,
    method,
    interval,
  });

  if (isPending) {
    return <Loading />;
  }
  if (error) {
    return <Alert severity="error">{error.message}</Alert>;
  }

  const valueFormatter = method === "pnl" ? currencyFormatter : percentFormatter;
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
        data: data.returns,
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

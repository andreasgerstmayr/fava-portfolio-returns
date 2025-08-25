import { Alert, useTheme } from "@mui/material";
import { createEnumParam, useQueryParam, withDefault } from "use-query-params";
import { useReturns } from "../api/returns";
import { Dashboard, DashboardRow, Panel } from "../components/Dashboard";
import { EChart } from "../components/EChart";
import { useToolbarContext } from "../components/Header/ToolbarProvider";
import { Loading } from "../components/Loading";
import { ReturnsMethod, ReturnsMethodSelection } from "../components/ReturnsMethodSelection";
import { getIntegerCurrencyFormatter, percentFormatter } from "../components/format";

const ReturnsMethodEnum = createEnumParam(["irr", "mdm", "twr", "monetary"]);
const ReturnsMethodParam = withDefault(ReturnsMethodEnum, "irr" as const);

export function Returns() {
  const [method, setMethod] = useQueryParam("method", ReturnsMethodParam);

  return (
    <Dashboard>
      <DashboardRow sx={{ justifyContent: "flex-end" }}>
        <ReturnsMethodSelection options={["irr", "mdm", "twr", "monetary"]} method={method} setMethod={setMethod} />
      </DashboardRow>
      <DashboardRow>
        <Panel title="Monthly Returns">
          <ReturnsHeatmapChart method={method} />
        </Panel>
      </DashboardRow>
      <DashboardRow>
        <Panel title="Yearly Returns">
          <ReturnsBarChart method={method} interval="yearly" />
        </Panel>
        <Panel title="Returns over Periods">
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
  const theme = useTheme();
  const { investmentFilter, targetCurrency } = useToolbarContext();
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
  const valueFormatter = method === "monetary" ? getIntegerCurrencyFormatter(targetCurrency) : percentFormatter;
  const monthFormatter = new Intl.DateTimeFormat(undefined, { month: "short" }).format;
  const option = {
    tooltip: {
      position: "top",
      valueFormatter,
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
      formatter: valueFormatter,
    },
    series: [
      {
        type: "heatmap",
        data: data.returns.map(([label, value]) => {
          if (!label.includes("-")) {
            return ["Entire Year", label, value];
          }

          const [year, month] = label.split("-");
          const monthLocale = monthFormatter(new Date(parseInt(year), parseInt(month) - 1, 1));

          // workaround to display -0.0000001 as 0 instead of -0
          const valueRounded = Math.round((value + Number.EPSILON) * 10000) / 10000 + 0;
          return [monthLocale, year, valueRounded];
        }),
        label: {
          show: true,
          formatter: (params: { data: [string, string, number] }) => valueFormatter(params.data[2]),
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
  const theme = useTheme();
  const { investmentFilter, targetCurrency } = useToolbarContext();
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

  const valueFormatter = method === "monetary" ? getIntegerCurrencyFormatter(targetCurrency) : percentFormatter;
  const option = {
    tooltip: {
      trigger: "axis",
      valueFormatter,
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
        name: "Returns",
        data: data.returns,
        itemStyle: {
          color: (params: { data: [string, number] }) => (params.data[1] >= 0 ? theme.pnl.profit : theme.pnl.loss),
        },
      },
    ],
  };

  return <EChart height="400px" option={option} />;
}

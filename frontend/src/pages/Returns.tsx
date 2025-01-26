import { Alert } from "@mui/material";
import { createEnumParam, useQueryParam, withDefault } from "use-query-params";
import { useSeries } from "../api/series";
import { Dashboard, DashboardRow, Panel } from "../components/Dashboard";
import { EChart } from "../components/EChart";
import { useToolbarContext } from "../components/Header/ToolbarProvider";
import { Loading } from "../components/Loading";
import { ReturnsMethods, ReturnsMethodSelection } from "../components/ReturnsMethodSelection";
import { NEGATIVE_NUMBER_COLOR, POSITIVE_NUMBER_COLOR } from "../components/style";

const ReturnsMethodEnum = createEnumParam(["irr", "twr"]);
const ReturnsMethodParam = withDefault(ReturnsMethodEnum, "irr" as const);

export function Returns() {
  const [method, setMethod] = useQueryParam("method", ReturnsMethodParam);

  return (
    <Dashboard>
      <DashboardRow sx={{ justifyContent: "flex-end" }}>
        <ReturnsMethodSelection options={["irr", "twr"]} method={method} setMethod={setMethod} />
      </DashboardRow>
      <DashboardRow>
        <Panel title="Monthly Returns" help={ReturnsMethods[method].help}>
          <ReturnsHeatmapChart seriesName={`returns_${method}_heatmap`} />
        </Panel>
      </DashboardRow>
      <DashboardRow>
        <Panel title="Yearly Returns">
          <ReturnsBarChart seriesName={`returns_${method}_yearly`} />
        </Panel>
        <Panel title="Returns over Periods">
          <ReturnsBarChart seriesName={`returns_${method}_periods`} />
        </Panel>
      </DashboardRow>
    </Dashboard>
  );
}

interface ReturnsHeatmapChartProps {
  seriesName: string;
}

function ReturnsHeatmapChart({ seriesName }: ReturnsHeatmapChartProps) {
  const { investmentFilter, targetCurrency } = useToolbarContext();
  const { isPending, error, data } = useSeries({
    investmentFilter,
    targetCurrency,
    series: [seriesName],
  });

  if (isPending) {
    return <Loading />;
  }
  if (error) {
    return <Alert severity="error">{error.message}</Alert>;
  }

  const percentFormatter = new Intl.NumberFormat(undefined, {
    style: "percent",
    maximumFractionDigits: 2,
    signDisplay: "exceptZero",
  }).format;
  const monthFormatter = new Intl.DateTimeFormat(undefined, { month: "short" }).format;

  const series = data.series[seriesName];

  const option = {
    tooltip: {
      position: "top",
      valueFormatter: percentFormatter,
    },
    grid: {
      bottom: "100", // space for visualMap
    },
    xAxis: {
      type: "category",
      splitArea: {
        show: true,
      },
    },
    yAxis: {
      type: "category",
      splitArea: {
        show: true,
      },
    },
    visualMap: {
      min: -0.15,
      max: 0.15,
      calculable: true, // show handles
      orient: "horizontal",
      left: "center",
      bottom: "0", // place visualMap at bottom of chart
      itemHeight: "400", // width
      inRange: {
        color: [NEGATIVE_NUMBER_COLOR, "#fff", POSITIVE_NUMBER_COLOR],
      },
      formatter: percentFormatter,
    },
    series: [
      {
        type: "heatmap",
        data: series.map(([label, value]) => {
          if (!label.includes("-")) {
            return ["Entire Year", label, value];
          }

          const [year, month] = label.split("-");
          const monthLocale = monthFormatter(new Date(parseInt(year), parseInt(month) - 1, 1));
          return [monthLocale, year, value];
        }),
        label: {
          show: true,
          formatter: (params: { data: [string, string, number] }) => percentFormatter(params.data[2]),
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

  const numRows = series.filter(([label]) => !label.includes("-")).length;
  const chartHeightPx = 170 + numRows * 40;

  return <EChart height={`${chartHeightPx}px`} option={option} />;
}

interface ReturnsBarChartProps {
  seriesName: string;
}

function ReturnsBarChart({ seriesName }: ReturnsBarChartProps) {
  const { investmentFilter, targetCurrency } = useToolbarContext();
  const { isPending, error, data } = useSeries({
    investmentFilter,
    targetCurrency,
    series: [seriesName],
  });

  if (isPending) {
    return <Loading />;
  }
  if (error) {
    return <Alert severity="error">{error.message}</Alert>;
  }

  const percentFormatter = new Intl.NumberFormat(undefined, {
    style: "percent",
    maximumFractionDigits: 2,
    signDisplay: "exceptZero",
  }).format;

  const series = data.series[seriesName];

  const option = {
    tooltip: {
      trigger: "axis",
      valueFormatter: percentFormatter,
    },
    xAxis: {
      type: "category",
    },
    yAxis: {
      type: "value",
      axisLabel: {
        formatter: percentFormatter,
      },
    },
    series: [
      {
        type: "bar",
        name: "Returns",
        data: series,
        itemStyle: {
          color: (params: { data: [string, number] }) =>
            params.data[1] >= 0 ? POSITIVE_NUMBER_COLOR : NEGATIVE_NUMBER_COLOR,
        },
      },
    ],
  };

  return <EChart height="400px" option={option} />;
}

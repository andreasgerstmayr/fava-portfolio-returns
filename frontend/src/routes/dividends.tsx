import { Alert } from "@mui/material";
import { createRoute, stripSearchParams } from "@tanstack/react-router";
import { EChartsOption } from "echarts";
import { z } from "zod";
import { useDividends } from "../api/dividends";
import { Dashboard, DashboardRow, Panel, PanelGroup, PanelGroupItem } from "../components/Dashboard";
import { EChart } from "../components/EChart";
import { useToolbarContext } from "../components/Header/ToolbarProvider";
import { Loading } from "../components/Loading";
import { anyFormatter, getCurrencyFormatter } from "../components/format";
import { useSearchParam } from "../components/useSearchParam";
import { RootRoute } from "./__root";

const searchSchema = z.object({
  interval: z.enum(["month", "year"]).default("month").catch("month"),
});

export const DividendsRoute = createRoute({
  getParentRoute: () => RootRoute,
  path: "dividends",
  validateSearch: searchSchema,
  search: {
    middlewares: [stripSearchParams({ interval: "month" })],
  },
  component: Dividends,
});

function Dividends() {
  const [interval, setInterval] = useSearchParam(DividendsRoute, "interval");

  return (
    <Dashboard>
      <DashboardRow>
        <PanelGroup active={interval} setActive={setInterval}>
          <PanelGroupItem id="month" label="monthly">
            <Panel title="Dividends">
              <DividendsChart interval="monthly" />
            </Panel>
          </PanelGroupItem>
          <PanelGroupItem id="year" label="yearly">
            <Panel title="Dividends">
              <DividendsChart interval="yearly" />
            </Panel>
          </PanelGroupItem>
        </PanelGroup>
      </DashboardRow>
    </Dashboard>
  );
}

interface DividendsChartProps {
  interval: "monthly" | "yearly";
}

function DividendsChart({ interval }: DividendsChartProps) {
  const { investmentFilter, targetCurrency } = useToolbarContext();
  const { isPending, error, data } = useDividends({
    investmentFilter,
    targetCurrency,
    interval,
  });

  if (isPending) {
    return <Loading />;
  }
  if (error) {
    return <Alert severity="error">{error.message}</Alert>;
  }

  const investments = new Set(data.chart.flatMap((v) => Object.keys(v)));
  investments.delete("date");
  if (investments.size === 0) {
    return <Alert severity="info">No dividends in this time frame.</Alert>;
  }

  const currencyFormatter = getCurrencyFormatter(targetCurrency);
  const option: EChartsOption = {
    tooltip: {
      valueFormatter: anyFormatter(currencyFormatter),
    },
    legend: {
      show: investments.size <= 10,
      bottom: 0,
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
      // required because not every row contains all investment names
      dimensions: ["date", ...investments],
    },
    series: [...investments].sort().map((investment) => ({
      type: "bar",
      name: investment,
      encode: { x: "date", y: investment },
      barMinWidth: 4,
      barMaxWidth: 20,
      stack: "dividends",
      emphasis: {
        focus: "series",
      },
    })),
  };

  return <EChart height="400px" option={option} />;
}

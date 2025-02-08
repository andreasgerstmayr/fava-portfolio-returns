import { Alert } from "@mui/material";
import { useDividends } from "../api/dividends";
import { Dashboard, DashboardRow, Panel, PanelGroup } from "../components/Dashboard";
import { EChart } from "../components/EChart";
import { useToolbarContext } from "../components/Header/ToolbarProvider";
import { Loading } from "../components/Loading";
import { getCurrencyFormatter } from "../components/format";

export function Dividends() {
  return (
    <Dashboard>
      <DashboardRow>
        <PanelGroup param="interval" labels={["monthly", "yearly"]}>
          <Panel title="Dividends">
            <DividendsChart interval="monthly" />
          </Panel>
          <Panel title="Dividends">
            <DividendsChart interval="yearly" />
          </Panel>
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

  const names = new Set(data.chart.flatMap((v) => Object.keys(v)));
  names.delete("date");
  if (names.size === 0) {
    return <Alert severity="info">No dividends in this time frame.</Alert>;
  }

  const currencyFormatter = getCurrencyFormatter(targetCurrency);
  const option = {
    tooltip: {
      valueFormatter: currencyFormatter,
    },
    legend: {
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
    },
    series: [...names].map((name) => ({
      type: "bar",
      name: name,
      dimensions: ["date", name],
      barMinWidth: 4,
      barMaxWidth: 20,
      stack: "dividends",
    })),
  };

  return <EChart height="400px" option={option} />;
}

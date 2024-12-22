import { Alert } from "@mui/material";
import { useDividends } from "../api/dividends";
import { Dashboard, DashboardRow, Panel, PanelGroup } from "../components/Dashboard";
import { EChart } from "../components/EChart";
import { useToolbarContext } from "../components/Header/ToolbarProvider";
import { Loading } from "../components/Loading";

export function Dividends() {
  return (
    <Dashboard>
      <DashboardRow>
        <PanelGroup labels={["monthly", "yearly"]}>
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

  const currencyFormatter = new Intl.NumberFormat(undefined, {
    style: "currency",
    currency: targetCurrency,
  }).format;

  const option = {
    tooltip: {
      valueFormatter: currencyFormatter,
    },
    legend: {
      bottom: 0,
    },
    xAxis: {
      type: "category",
      data: data.intervals,
    },
    yAxis: {
      type: "value",
      axisLabel: {
        formatter: currencyFormatter,
      },
    },
    series: Object.entries(data.dividends).map(([name, dividends]) => ({
      type: "bar",
      name: name,
      data: data.intervals.map((i) => dividends[i]),
      barMaxWidth: 20,
      stack: "dividends",
    })),
  };

  return <EChart height="400px" option={option} />;
}

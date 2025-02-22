import { Alert } from "@mui/material";
import { useCashFlows } from "../api/cash_flows";
import { Dashboard, DashboardRow, Panel, PanelGroup } from "../components/Dashboard";
import { EChart } from "../components/EChart";
import { useToolbarContext } from "../components/Header/ToolbarProvider";
import { Loading } from "../components/Loading";
import { getCurrencyFormatter, numberFormatter, timestampToMonth, timestampToYear } from "../components/format";

export function CashFlows() {
  return (
    <Dashboard>
      <DashboardRow>
        <PanelGroup param="interval" labels={["monthly", "yearly"]}>
          <Panel
            title="Cash Flows"
            help="The cash flow chart shows all incoming and outgoing cashflows of an investment."
          >
            <CashFlowsChart interval="monthly" />
          </Panel>
          <Panel
            title="Cash Flows"
            help="The cash flow chart shows all incoming and outgoing cashflows of an investment."
          >
            <CashFlowsChart interval="yearly" />
          </Panel>
        </PanelGroup>
      </DashboardRow>
      <DashboardRow>
        <Panel title="List of Cash Flows">
          <CashFlowsTable />
        </Panel>
      </DashboardRow>
    </Dashboard>
  );
}

interface CashFlowsChartProps {
  interval: "monthly" | "yearly";
}
function CashFlowsChart({ interval }: CashFlowsChartProps) {
  const { investmentFilter, targetCurrency } = useToolbarContext();
  const { isPending, error, data } = useCashFlows({ investmentFilter, targetCurrency, interval });

  if (isPending) {
    return <Loading />;
  }
  if (error) {
    return <Alert severity="error">{error.message}</Alert>;
  }

  if (data.table.length === 0) {
    return <Alert severity="info">No cash flows in this time frame.</Alert>;
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
    xAxis: {
      type: "time",
      axisPointer: {
        label: {
          formatter: ({ value }: { value: number }) =>
            interval === "monthly" ? timestampToMonth(value) : timestampToYear(value),
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
      source: data.chart,
    },
    series: [
      {
        type: "bar",
        name: "Cash flows excl. dividends",
        dimensions: ["date", "exdiv"],
        barMinWidth: 4,
        barMaxWidth: 20,
        stack: "flows",
      },
      {
        type: "bar",
        name: "Dividends",
        dimensions: ["date", "div"],
        barMinWidth: 4,
        barMaxWidth: 20,
        stack: "flows",
      },
    ],
  };

  return <EChart height="400px" option={option} />;
}

function CashFlowsTable() {
  const { investmentFilter, targetCurrency } = useToolbarContext();
  const { isPending, error, data } = useCashFlows({ investmentFilter, targetCurrency, interval: "monthly" });

  if (isPending) {
    return <Loading />;
  }
  if (error) {
    return <Alert severity="error">{error.message}</Alert>;
  }

  if (data.table.length === 0) {
    return <Alert severity="info">No cash flows in this time frame.</Alert>;
  }

  return (
    <table>
      <thead>
        <tr>
          <th>Date</th>
          <th>Amount</th>
          <th>Dividend</th>
          <th>Source</th>
          <th>Investment</th>
          <th>Transaction</th>
        </tr>
      </thead>
      <tbody>
        {data.table.map((flow, i) => (
          <tr key={i}>
            <td>{flow.date}</td>
            <td className="num">
              {numberFormatter(flow.amount.number)} {flow.amount.currency}
            </td>
            <td>{flow.isDividend ? "yes" : "no"}</td>
            <td>{flow.source}</td>
            <td>{flow.account}</td>
            <td>{flow.transaction}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

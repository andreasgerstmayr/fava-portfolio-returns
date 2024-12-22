import { Alert } from "@mui/material";
import { useCashFlows } from "../api/cash_flows";
import { useSeries } from "../api/series";
import { Dashboard, DashboardRow, Panel } from "../components/Dashboard";
import { EChart } from "../components/EChart";
import { useToolbarContext } from "../components/Header/ToolbarProvider";
import { Loading } from "../components/Loading";

export function CashFlows() {
  return (
    <Dashboard>
      <DashboardRow>
        <Panel
          title="Cash Flows"
          help="The cash flow chart shows all incoming and outgoing cashflows of an investment."
        >
          <CashFlowsChart />
        </Panel>
      </DashboardRow>
      <DashboardRow>
        <Panel title="List of Cash Flows">
          <CashFlowsTable />
        </Panel>
      </DashboardRow>
    </Dashboard>
  );
}

function CashFlowsChart() {
  const { investmentFilter, targetCurrency } = useToolbarContext();
  const { isPending, error, data } = useSeries({
    investmentFilter,
    targetCurrency,
    series: ["cash_flows_exdiv", "cash_flows_div"],
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

  const cashFlowsExDiv = data.series["cash_flows_exdiv"];
  const cashFlowsDiv = data.series["cash_flows_div"];

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
    },
    yAxis: {
      type: "value",
      axisLabel: {
        formatter: currencyFormatter,
      },
    },
    series: [
      {
        type: "bar",
        name: "Cash flows excl. dividends",
        data: cashFlowsExDiv,
        barMinWidth: 4,
        barMaxWidth: 20,
        stack: "flows",
      },
      {
        type: "bar",
        name: "Dividends",
        data: cashFlowsDiv,
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
  const { isPending, error, data } = useCashFlows({ investmentFilter, targetCurrency });

  if (isPending) {
    return <Loading />;
  }
  if (error) {
    return <Alert severity="error">{error.message}</Alert>;
  }

  const numberFormatter = new Intl.NumberFormat(undefined, {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format;

  return (
    <table>
      <thead>
        <tr>
          <th>Date</th>
          <th>Amount</th>
          <th>Dividend</th>
          <th>Source</th>
          <th>Investment</th>
        </tr>
      </thead>
      <tbody>
        {data.cashFlows.map((flow, i) => (
          <tr key={i}>
            <td>{flow.date}</td>
            <td className="num">
              {numberFormatter(flow.amount.number)} {flow.amount.currency}
            </td>
            <td>{flow.isDividend ? "yes" : "no"}</td>
            <td>{flow.source}</td>
            <td>{flow.account}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

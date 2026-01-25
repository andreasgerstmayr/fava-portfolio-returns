import { Alert } from "@mui/material";
import { createRoute, stripSearchParams } from "@tanstack/react-router";
import { EChartsOption } from "echarts";
import { useTranslation } from "react-i18next";
import { z } from "zod";
import { useCashFlows } from "../api/cash_flows";
import { Dashboard, DashboardRow, Panel, PanelGroup, PanelGroupItem } from "../components/Dashboard";
import { EChart } from "../components/EChart";
import { useToolbarContext } from "../components/Header/ToolbarProvider";
import { Loading } from "../components/Loading";
import {
  anyFormatter,
  timestampToMonth,
  timestampToYear,
  useCurrencyFormatter,
  useNumberFormatter,
} from "../components/format";
import { useSearchParam } from "../components/useSearchParam";
import { RootRoute } from "./__root";

const searchSchema = z.object({
  interval: z.enum(["month", "year"]).default("month").catch("month"),
});

export const CashFlowsRoute = createRoute({
  getParentRoute: () => RootRoute,
  path: "cash_flows",
  validateSearch: searchSchema,
  search: {
    middlewares: [stripSearchParams({ interval: "month" })],
  },
  component: CashFlows,
});

function CashFlows() {
  const { t } = useTranslation();
  const [interval, setInterval] = useSearchParam(CashFlowsRoute, "interval");

  return (
    <Dashboard>
      <DashboardRow>
        <PanelGroup active={interval} setActive={setInterval}>
          <PanelGroupItem id="month" label={t("monthly")}>
            <Panel
              title={t("Cash Flows")}
              help={t("The cash flow chart shows all incoming and outgoing cashflows of an investment.")}
            >
              <CashFlowsChart interval="monthly" />
            </Panel>
          </PanelGroupItem>
          <PanelGroupItem id="year" label={t("yearly")}>
            <Panel
              title={t("Cash Flows")}
              help={t("The cash flow chart shows all incoming and outgoing cashflows of an investment.")}
            >
              <CashFlowsChart interval="yearly" />
            </Panel>
          </PanelGroupItem>
        </PanelGroup>
      </DashboardRow>
      <DashboardRow>
        <Panel title={t("List of Cash Flows")}>
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
  const { t } = useTranslation();
  const { investmentFilter, targetCurrency } = useToolbarContext();
  const currencyFormatter = useCurrencyFormatter(targetCurrency);
  const { isPending, error, data } = useCashFlows({ investmentFilter, targetCurrency, interval });

  if (isPending) {
    return <Loading />;
  }
  if (error) {
    return <Alert severity="error">{error.message}</Alert>;
  }

  if (data.table.length === 0) {
    return <Alert severity="info">{t("No cash flows in this time frame.")}</Alert>;
  }

  const option: EChartsOption = {
    tooltip: {
      trigger: "axis",
      valueFormatter: anyFormatter(currencyFormatter),
    },
    legend: {
      bottom: 0,
    },
    xAxis: {
      type: "time",
      axisPointer: {
        label: {
          formatter: (params) =>
            interval === "monthly" ? timestampToMonth(params.value as number) : timestampToYear(params.value as number),
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
        name: t("Cash flows excl. dividends"),
        encode: { x: "date", y: "exdiv" },
        barMinWidth: 4,
        barMaxWidth: 20,
        stack: "flows",
      },
      {
        type: "bar",
        name: t("Dividends"),
        encode: { x: "date", y: "div" },
        barMinWidth: 4,
        barMaxWidth: 20,
        stack: "flows",
      },
    ],
  };

  return <EChart height="400px" option={option} />;
}

function CashFlowsTable() {
  const { t } = useTranslation();
  const { investmentFilter, targetCurrency } = useToolbarContext();
  const numberFormatter = useNumberFormatter();
  const { isPending, error, data } = useCashFlows({ investmentFilter, targetCurrency, interval: "monthly" });

  if (isPending) {
    return <Loading />;
  }
  if (error) {
    return <Alert severity="error">{error.message}</Alert>;
  }

  if (data.table.length === 0) {
    return <Alert severity="info">{t("No cash flows in this time frame.")}</Alert>;
  }

  return (
    <table>
      <thead>
        <tr>
          <th>{t("Date")}</th>
          <th>{t("Amount")}</th>
          <th>{t("Dividend")}</th>
          <th>{t("Source")}</th>
          <th>{t("Investment")}</th>
          <th>{t("Transaction")}</th>
        </tr>
      </thead>
      <tbody>
        {data.table.map((flow, i) => (
          <tr key={i}>
            <td>{flow.date}</td>
            <td className="num">
              {numberFormatter(flow.amount.number)} {flow.amount.currency}
            </td>
            <td>{flow.isDividend ? t("yes") : t("no")}</td>
            <td>{flow.source}</td>
            <td>{flow.account}</td>
            <td>{flow.transaction}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

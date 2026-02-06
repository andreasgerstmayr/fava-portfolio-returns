import { createRoute, stripSearchParams } from "@tanstack/react-router";
import { useTranslation } from "react-i18next";
import { z } from "zod";
import { Dashboard, DashboardRow, Panel } from "../components/Dashboard";
import { MetricName, MetricSelection } from "../components/MetricSelection";
import { useSearchParam } from "../components/useSearchParam";
import { RootRoute } from "./__root";
import { MetricBarChart, MetricHeatmapChart } from "./metrics";

const supportedMetrics: MetricName[] = ["irr", "mdm", "twr", "pnl"];
const searchSchema = z.object({
  metric: z.enum(supportedMetrics).default("irr").catch("irr"),
});

export const ReturnsRoute = createRoute({
  getParentRoute: () => RootRoute,
  path: "returns",
  validateSearch: searchSchema,
  search: {
    middlewares: [stripSearchParams({ metric: "irr" })],
  },
  component: Returns,
});

function Returns() {
  const { t } = useTranslation();
  const [metric, setMetric] = useSearchParam(ReturnsRoute, "metric");

  return (
    <Dashboard>
      <DashboardRow sx={{ justifyContent: "flex-end" }}>
        <MetricSelection options={supportedMetrics} value={metric} setValue={setMetric} />
      </DashboardRow>
      <DashboardRow>
        <Panel title={t("Monthly Returns")}>
          <MetricHeatmapChart metric={metric} />
        </Panel>
      </DashboardRow>
      <DashboardRow>
        <Panel title={t("Yearly Returns")}>
          <MetricBarChart metric={metric} interval="yearly" />
        </Panel>
        <Panel title={t("Returns over Periods")}>
          <MetricBarChart metric={metric} interval="periods" />
        </Panel>
      </DashboardRow>
    </Dashboard>
  );
}

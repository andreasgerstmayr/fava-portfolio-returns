import { createRoute, stripSearchParams } from "@tanstack/react-router";
import { useTranslation } from "react-i18next";
import { z } from "zod";
import { Dashboard, DashboardRow, Panel } from "../components/Dashboard";
import { useSearchParam } from "../components/useSearchParam";
import { RootRoute } from "./__root";
import { InvestmentsTable } from "./investments";

const searchSchema = z.object({
  liquidated: z.boolean().default(false).catch(false),
});

export const GroupsRoute = createRoute({
  getParentRoute: () => RootRoute,
  path: "groups",
  validateSearch: searchSchema,
  search: {
    middlewares: [stripSearchParams({ liquidated: false })],
  },
  staticData: {
    showInvestmentsSelection: false,
    showCurrencySelection: false,
  },
  component: Groups,
});

function Groups() {
  const { t } = useTranslation();
  const [includeLiquidated, setIncludeLiquidated] = useSearchParam(GroupsRoute, "liquidated");

  return (
    <Dashboard>
      <DashboardRow>
        <Panel title={t("Groups")} help={t("Lists the groups defined in the beangrow configuration file.")}>
          <InvestmentsTable
            groupBy="group"
            includeLiquidated={includeLiquidated}
            setIncludeLiquidated={setIncludeLiquidated}
          />
        </Panel>
      </DashboardRow>
    </Dashboard>
  );
}

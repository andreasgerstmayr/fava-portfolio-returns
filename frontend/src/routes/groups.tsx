import { createRoute, stripSearchParams } from "@tanstack/react-router";
import { fallback, zodValidator } from "@tanstack/zod-adapter";
import { z } from "zod";
import { Dashboard, DashboardRow, Panel } from "../components/Dashboard";
import { useSearchParam } from "../components/useSearchParam";
import { RootRoute } from "./__root";
import { InvestmentsTable } from "./investments";

const groupsSchema = z.object({
  liquidated: fallback(z.boolean(), false).default(false),
});

export const GroupsRoute = createRoute({
  getParentRoute: () => RootRoute,
  path: "groups",
  validateSearch: zodValidator(groupsSchema),
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
  const [includeLiquidated, setIncludeLiquidated] = useSearchParam(GroupsRoute, "liquidated");

  return (
    <Dashboard>
      <DashboardRow>
        <Panel title="Groups" help="Lists the groups defined in the beangrow configuration file.">
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

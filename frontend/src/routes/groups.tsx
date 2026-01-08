import { Dashboard, DashboardRow, Panel } from "../components/Dashboard";
import { InvestmentsTable } from "./investments";

export function Groups() {
  return (
    <Dashboard>
      <DashboardRow>
        <Panel title="Groups" help="Lists the groups defined in the beangrow configuration file.">
          <InvestmentsTable groupBy="group" />
        </Panel>
      </DashboardRow>
    </Dashboard>
  );
}

import { InvestmentsSelection } from "../InvestmentsSelection";
import { useToolbarContext } from "./ToolbarProvider";

export function GlobalInvestmentsSelection() {
  const { investmentFilter, setInvestmentFilter } = useToolbarContext();
  return (
    <InvestmentsSelection
      label="Investments Filter"
      types={["Group", "Account", "Currency"]}
      investments={investmentFilter}
      setInvestments={setInvestmentFilter}
    />
  );
}

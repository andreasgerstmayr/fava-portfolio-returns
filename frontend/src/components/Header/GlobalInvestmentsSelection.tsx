import { InvestmentsSelection } from "../InvestmentsSelection";
import { useToolbarContext } from "./ToolbarProvider";

export function GlobalInvestmentsSelection() {
  const { investmentFilter: selectedInvestments, setInvestmentFilter: setSelectedInvestments } = useToolbarContext();
  return (
    <InvestmentsSelection
      label="Investments Filter"
      types={["Group", "Account", "InvestmentCurrency"]}
      investments={selectedInvestments}
      setInvestments={setSelectedInvestments}
    />
  );
}

import { useTranslation } from "react-i18next";
import { InvestmentsSelection } from "../InvestmentsSelection";
import { useToolbarContext } from "./ToolbarProvider";

export function GlobalInvestmentsSelection() {
  const { t } = useTranslation();
  const { investmentFilter, setInvestmentFilter } = useToolbarContext();
  return (
    <InvestmentsSelection
      label={t("Investments Filter")}
      types={["Group", "Account", "Currency"]}
      investments={investmentFilter}
      setInvestments={setInvestmentFilter}
    />
  );
}

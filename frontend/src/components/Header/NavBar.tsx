import { NavLink } from "react-router";
import { useToolbarContext } from "./ToolbarProvider";

export function NavBar() {
  const { investmentFilter: selectedInvestments, targetCurrency } = useToolbarContext();
  const toolbarParams = new URLSearchParams({ investments: selectedInvestments.join(","), currency: targetCurrency });

  return (
    <div className="headerline">
      <h3>
        <NavLink to={`/portfolio?${toolbarParams}`}>Portfolio</NavLink>
      </h3>
      <h3>
        <NavLink to={`/performance?${toolbarParams}`}>Performance</NavLink>
      </h3>
      <h3>
        <NavLink to={`/returns?${toolbarParams}`}>Returns</NavLink>
      </h3>
      <h3>
        <NavLink to={`/dividends?${toolbarParams}`}>Dividends</NavLink>
      </h3>
      <h3>
        <NavLink to={`/cash_flows?${toolbarParams}`}>Cash Flows</NavLink>
      </h3>
      <h3>
        <NavLink to={`/groups`}>Groups</NavLink>
      </h3>
    </div>
  );
}

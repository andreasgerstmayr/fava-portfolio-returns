import { NavLink } from "react-router";
import { useToolbarContext } from "./ToolbarProvider";

export function NavBar() {
  const { investmentFilter, targetCurrency, config } = useToolbarContext();
  const toolbarParams = new URLSearchParams();
  if (investmentFilter.length > 0) {
    toolbarParams.set("investments", investmentFilter.join(","));
  }
  if (targetCurrency !== config.operatingCurrencies[0]) {
    toolbarParams.set("currency", targetCurrency);
  }

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
      <h3>
        <NavLink to={`/investments`}>Investments</NavLink>
      </h3>
      <h3>
        <NavLink to={`/missing_prices`}>Missing Prices</NavLink>
      </h3>
      <h3>
        <NavLink to={`/help`}>Help</NavLink>
      </h3>
    </div>
  );
}

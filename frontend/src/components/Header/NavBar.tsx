import { Box } from "@mui/material";
import { Link } from "@tanstack/react-router";
import { retainSearchParams } from "../../routes/__root";

export function NavBar() {
  return (
    <Box className="headerline" sx={{ ".active": { color: "inherit" } }}>
      <h3>
        <Link to="/portfolio" search={retainSearchParams}>
          Portfolio
        </Link>
      </h3>
      <h3>
        <Link to="/performance" search={retainSearchParams}>
          Performance
        </Link>
      </h3>
      <h3>
        <Link to="/returns" search={retainSearchParams}>
          Returns
        </Link>
      </h3>
      <h3>
        <Link to="/dividends" search={retainSearchParams}>
          Dividends
        </Link>
      </h3>
      <h3>
        <Link to="/cash_flows" search={retainSearchParams}>
          Cash Flows
        </Link>
      </h3>
      <h3>
        <Link to="/groups" search={retainSearchParams}>
          Groups
        </Link>
      </h3>
      <h3>
        <Link to="/investments" search={retainSearchParams}>
          Investments
        </Link>
      </h3>
      <h3>
        <Link to="/missing_prices" search={retainSearchParams}>
          Missing Prices
        </Link>
      </h3>
      <h3>
        <Link to="/help" search={retainSearchParams}>
          Help
        </Link>
      </h3>
    </Box>
  );
}

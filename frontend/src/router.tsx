import { createHashRouter, Navigate } from "react-router";
import { CashFlows } from "./routes/cash_flows";
import { Dividends } from "./routes/dividends";
import { Groups } from "./routes/groups";
import { Help } from "./routes/help";
import { Investments } from "./routes/investments";
import { MissingPrices } from "./routes/missing_prices";
import { Performance } from "./routes/performance";
import { Portfolio } from "./routes/portfolio";
import { Returns } from "./routes/returns";
import { Layout } from "./routes/root";

export const router = createHashRouter([
  {
    path: "/",
    element: <Layout />,
    children: [
      { index: true, element: <Navigate to="/portfolio" replace /> },
      {
        path: "portfolio",
        element: <Portfolio />,
      },
      {
        path: "performance",
        element: <Performance />,
      },
      {
        path: "returns",
        element: <Returns />,
      },
      {
        path: "dividends",
        element: <Dividends />,
      },
      {
        path: "cash_flows",
        element: <CashFlows />,
      },
      {
        path: "groups",
        element: <Groups />,
        handle: { showInvestmentsSelection: false, showCurrencySelection: false },
      },
      {
        path: "investments",
        element: <Investments />,
        handle: { showInvestmentsSelection: false },
      },
      {
        path: "missing_prices",
        element: <MissingPrices />,
        handle: { showInvestmentsSelection: false, showDateRangeSelection: false, showCurrencySelection: false },
      },
      {
        path: "help",
        element: <Help />,
        handle: { showInvestmentsSelection: false, showDateRangeSelection: false, showCurrencySelection: false },
      },
    ],
  },
]);

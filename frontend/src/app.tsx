import { createTheme, ThemeProvider } from "@mui/material";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { createRoot } from "react-dom/client";
import { createHashRouter, Navigate, RouterProvider } from "react-router";
import { CashFlows } from "./pages/CashFlows";
import { Dividends } from "./pages/Dividends";
import { Help } from "./pages/Help";
import { Groups, Investments } from "./pages/Investments";
import { Layout } from "./pages/Layout";
import { MissingPrices } from "./pages/MissingPrices";
import { Performance } from "./pages/Performance";
import { Portfolio } from "./pages/Portfolio";
import { Returns } from "./pages/Returns";

const router = createHashRouter([
  {
    path: "/",
    element: <Layout />,
    children: [
      { path: "/", element: <Navigate to="/portfolio" replace /> },
      {
        path: "/portfolio",
        element: <Portfolio />,
      },
      {
        path: "/performance",
        element: <Performance />,
      },
      {
        path: "/returns",
        element: <Returns />,
      },
      {
        path: "/dividends",
        element: <Dividends />,
      },
      {
        path: "/cash_flows",
        element: <CashFlows />,
      },
      {
        path: "/groups",
        element: <Groups />,
        handle: { showInvestmentsSelection: false, showCurrencySelection: false },
      },
      {
        path: "/investments",
        element: <Investments />,
        handle: { showInvestmentsSelection: false },
      },
      {
        path: "/missing_prices",
        element: <MissingPrices />,
        handle: { showInvestmentsSelection: false, showCurrencySelection: false },
      },
      {
        path: "/help",
        element: <Help />,
        handle: { showInvestmentsSelection: false, showCurrencySelection: false },
      },
    ],
  },
]);

const theme = createTheme({
  cssVariables: true,
  colorSchemes: {
    dark: true
  },
  typography: {
    fontFamily: "",
  },
});

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: false,
    },
  },
});

export function renderApp(container: Element) {
  const root = createRoot(container);
  root.render(
    <ThemeProvider theme={theme}>
      <QueryClientProvider client={queryClient}>
        <RouterProvider router={router} />
      </QueryClientProvider>
    </ThemeProvider>,
  );
}

import { createBrowserHistory, parseHref } from "@tanstack/history";
import { createRouter } from "@tanstack/react-router";
import { IndexRoute } from "./routes";
import { RootRoute } from "./routes/__root";
import { CashFlowsRoute } from "./routes/cash_flows";
import { DividendsRoute } from "./routes/dividends";
import { GroupsRoute } from "./routes/groups";
import { HelpRoute } from "./routes/help";
import { InvestmentsRoute } from "./routes/investments";
import { MetricsRoute } from "./routes/metrics";
import { MissingPricesRoute } from "./routes/missing_prices";
import { PerformanceRoute } from "./routes/performance";
import { PortfolioRoute } from "./routes/portfolio";
import { ReturnsRoute } from "./routes/returns";

declare module "@tanstack/react-router" {
  interface Register {
    router: typeof router;
  }

  interface StaticDataRouteOption {
    showInvestmentsSelection?: boolean;
    showDateRangeSelection?: boolean;
    showCurrencySelection?: boolean;
  }
}

const basepath = getExtensionPath();

const routeTree = RootRoute.addChildren([
  IndexRoute,
  PortfolioRoute,
  PerformanceRoute,
  ReturnsRoute,
  MetricsRoute,
  DividendsRoute,
  CashFlowsRoute,
  GroupsRoute,
  InvestmentsRoute,
  MissingPricesRoute,
  HelpRoute,
]);

const browserHistory = createBrowserHistory({
  createHref: (originalPath: string) => {
    if (!originalPath.startsWith(basepath)) {
      return originalPath;
    }

    // transform /beancount/extension/FavaPortfolioReturns/performance to /beancount/extension/FavaPortfolioReturns/?path=performance
    const url = new URL(originalPath, location.href);
    const internalPath = url.pathname.substring(basepath.length + 1);
    url.searchParams.append("path", internalPath);
    return `${basepath}/?${url.searchParams}`;
  },
  parseLocation: () => {
    const url = new URL(location.href);
    if (!url.pathname.startsWith(basepath)) {
      return parseHref(`${url.pathname}${url.search}${url.hash}`, history.state);
    }

    // transform /beancount/extension/FavaPortfolioReturns/?path=performance to /beancount/extension/FavaPortfolioReturns/performance
    const pathParam = url.searchParams.get("path") ?? "";
    url.searchParams.delete("path");
    const pathname = `${basepath}/${pathParam}`;
    return parseHref(`${pathname}${url.search}${url.hash}`, history.state);
  },
});

export const router = createRouter({
  routeTree,
  history: browserHistory,
  basepath,
});

function getExtensionPath() {
  const path = location.pathname;
  const file = path.split("/")[1];
  return `/${file}/extension/FavaPortfolioReturns`;
}

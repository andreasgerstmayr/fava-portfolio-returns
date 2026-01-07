import { createRootRoute, Outlet } from "@tanstack/react-router";
import { TanStackRouterDevtools } from "@tanstack/react-router-devtools";
import { z } from "zod";
import { NavBar } from "../components/Header/NavBar";
import { Toolbar } from "../components/Header/Toolbar";
import { ToolbarProvider } from "../components/Header/ToolbarProvider";

// https://github.com/beancount/fava/blob/b12a90c7645e702b0d398292bdddd90645e31a88/frontend/src/stores/url.ts#L41-L48
const retained_fava_search_params = ["account", "charts", "conversion", "filter", "interval", "time"];
const retained_search_params = [...retained_fava_search_params, "investments", "currency"];

// Workaround for broken retainSearchParams middleware
// https://github.com/TanStack/router/issues/5292
// https://github.com/TanStack/router/issues/2845
export function retainSearchParams(prev: Record<string, unknown>) {
  return Object.fromEntries(Object.entries(prev).filter(([key]) => retained_search_params.includes(key)));
}

const searchSchema = z.object({
  // 2020 is parsed as number, 2020-01 is parsed as string
  time: z.union([z.string(), z.number()]).optional(),

  investments: z.string().optional(),
  currency: z.string().optional(),
});

export const RootRoute = createRootRoute({
  validateSearch: searchSchema,
  component: Layout,
});

function Layout() {
  return (
    <ToolbarProvider>
      <NavBar />
      <Toolbar />
      <Outlet />
      <TanStackRouterDevtools />
    </ToolbarProvider>
  );
}

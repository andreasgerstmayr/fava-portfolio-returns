import { createRoute, redirect } from "@tanstack/react-router";
import { retainSearchParams, RootRoute } from "./__root";

export const IndexRoute = createRoute({
  getParentRoute: () => RootRoute,
  path: "/",
  loader: async () => {
    throw redirect({ to: "/portfolio", search: retainSearchParams });
  },
});

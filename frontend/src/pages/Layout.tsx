import { Outlet } from "react-router";
import { QueryParamProvider } from "use-query-params";
import { NavBar } from "../components/Header/NavBar";
import { Toolbar } from "../components/Header/Toolbar";
import { ToolbarProvider } from "../components/Header/ToolbarProvider";
import { ReactRouterAdapter } from "../components/react_router_adapter";

export function Layout() {
  return (
    <QueryParamProvider adapter={ReactRouterAdapter}>
      <ToolbarProvider>
        <NavBar />
        <Toolbar />
        <Outlet />
      </ToolbarProvider>
    </QueryParamProvider>
  );
}

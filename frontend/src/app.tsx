import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { RouterProvider } from "@tanstack/react-router";
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "./i18n";
import { router } from "./router";

// When navigating from this extension to another Fava page, Fava removes the node from the DOM.
// However, React is still mounted in this (now detached) node.
// Therefore, let's render React once into a detached node, and when the extension is visible, attach this node to the DOM tree.
let appContainer: HTMLDivElement | null = null;
export function renderApp(container: Element) {
  if (!appContainer) {
    appContainer = document.createElement("div");
    const root = createRoot(appContainer);
    root.render(
      <StrictMode>
        <App />
      </StrictMode>,
    );
  }

  container.replaceChildren(appContainer);
}

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: false,
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router} />
    </QueryClientProvider>
  );
}

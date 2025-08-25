import { createTheme, ThemeProvider } from "@mui/material";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { createRoot } from "react-dom/client";
import { RouterProvider } from "react-router";
import { useConfig } from "./api/config";
import { PNL_COLOR_SCHEME, PNLColorScheme, PNLColorSchemeVariant } from "./components/format";
import { router } from "./router";

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
    <QueryClientProvider client={queryClient}>
      <CustomThemeProvider>
        <RouterProvider router={router} />
      </CustomThemeProvider>
    </QueryClientProvider>,
  );
}

interface CustomThemeProviderProps {
  children?: React.ReactNode;
}

// extend Material-UI theme
declare module "@mui/material/styles" {
  interface Theme {
    "return-colors": PNLColorScheme;
  }
  interface ThemeOptions {
    "return-colors"?: PNLColorScheme;
  }
}

function CustomThemeProvider(props: CustomThemeProviderProps) {
  const { children } = props;
  const config = useConfig();
  const storedThemeSetting = document.documentElement.style.colorScheme;
  const isDarkMode =
    storedThemeSetting == "dark" ||
    (window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches && storedThemeSetting != "light");

  const pnlColor: PNLColorSchemeVariant = config.data?.swapColors ? "red-green" : "green-red";
  const theme = createTheme({
    cssVariables: true,
    palette: {
      mode: isDarkMode ? "dark" : "light",
    },
    typography: {
      fontFamily: "", // use default Fava font instead of MUI font
    },
    "return-colors": PNL_COLOR_SCHEME[pnlColor],
  });

  return <ThemeProvider theme={theme}>{children}</ThemeProvider>;
}

import { createTheme, ThemeProvider, useMediaQuery } from "@mui/material";
import { useConfig } from "./api/config";

// extend Material-UI theme
declare module "@mui/material/styles" {
  interface Theme {
    pnl: PNLColorScheme["pnl"];
    trend: PNLColorScheme["trend"];
  }
}

// Base colors from fava
const BASE_RED = "#af3d3d";
const BASE_GREEN = "#3daf46";

// colors from https://mui.com/material-ui/getting-started/templates/dashboard/
const BASE_GREEN_TREND = `120, 44%, 53%`;
const BASE_RED_TREND = `0, 90%, 40%`;

export interface PNLColorScheme {
  pnl: {
    /** profit color */
    profit: string;
    /** loss color */
    loss: string;
  };
  trend: {
    /** positive trend color */
    positive: (opacity?: number) => string;
    /** negative trend color */
    negative: (opacity?: number) => string;
  };
}

export type PNLColorSchemeVariant = "green-red" | "red-green";

const PNL_COLOR_SCHEMES: Record<PNLColorSchemeVariant, PNLColorScheme> = {
  "green-red": {
    pnl: {
      profit: BASE_GREEN,
      loss: BASE_RED,
    },
    trend: {
      positive(opacity = 1) {
        return `hsla(${BASE_GREEN_TREND}, ${opacity})`;
      },
      negative(opacity = 1) {
        return `hsla(${BASE_RED_TREND}, ${opacity})`;
      },
    },
  },
  "red-green": {
    pnl: {
      profit: BASE_RED,
      loss: BASE_GREEN,
    },
    trend: {
      positive(opacity = 1) {
        return `hsla(${BASE_RED_TREND}, ${opacity})`;
      },
      negative(opacity = 1) {
        return `hsla(${BASE_GREEN_TREND}, ${opacity})`;
      },
    },
  },
};

interface CustomThemeProviderProps {
  children?: React.ReactNode;
}

export function CustomThemeProvider({ children }: CustomThemeProviderProps) {
  const { data: config } = useConfig();
  const prefersDark = useMediaQuery("(prefers-color-scheme: dark)");
  const themeName = getFavaThemeSetting() ?? (prefersDark ? "dark" : "light");

  const defaultPnLColor = getDefaultPnlColorScheme();
  const pnlColorScheme =
    config?.pnlColorScheme && config.pnlColorScheme in PNL_COLOR_SCHEMES
      ? PNL_COLOR_SCHEMES[config.pnlColorScheme]
      : PNL_COLOR_SCHEMES[defaultPnLColor];

  const theme = createTheme({
    cssVariables: true,
    palette: {
      mode: themeName,
    },
    typography: {
      fontFamily: "", // use default Fava font instead of MUI font
    },
    ...pnlColorScheme,
  });

  return <ThemeProvider theme={theme}>{children}</ThemeProvider>;
}

function getFavaThemeSetting(): "light" | "dark" | undefined {
  const favaThemeSetting = document.documentElement.style.colorScheme;
  switch (favaThemeSetting) {
    case "light":
      return "light";
    case "dark":
      return "dark";
    default:
      return undefined;
  }
}

/**
 * Default pnl color scheme
 *
 * Use red-green color scheme for China and Japan, green-red for other regions
 */
function getDefaultPnlColorScheme() {
  const locale = new Intl.Locale(navigator.language);
  switch (locale.region) {
    case "CN":
    case "JP":
      return "red-green";
    default:
      return "green-red";
  }
}

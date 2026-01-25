import { Alert, Box, CircularProgress } from "@mui/material";
import { createContext, useContext, useEffect } from "react";
import { useTranslation } from "react-i18next";
import { ConfigResponse, useConfig } from "../../api/config";

export interface ConfigContextType {
  config: ConfigResponse;
}

const ConfigContext = createContext<ConfigContextType | undefined>(undefined);

interface ConfigProviderProps {
  children?: React.ReactNode;
}

export function ConfigProvider({ children }: ConfigProviderProps) {
  const { i18n } = useTranslation();
  const { isPending, error, data: config } = useConfig();

  useEffect(() => {
    if (!config?.language) {
      return;
    }
    i18n.changeLanguage(config.language);
  }, [i18n, config?.language]);

  if (isPending) {
    return (
      <Box sx={{ display: "flex", justifyContent: "center", my: 5 }}>
        <CircularProgress />
      </Box>
    );
  }
  if (error) {
    return <Alert severity="error">{error.message}</Alert>;
  }

  return <ConfigContext.Provider value={{ config }}>{children}</ConfigContext.Provider>;
}

export function useConfigContext(): ConfigContextType {
  const ctx = useContext(ConfigContext);
  if (ctx === undefined) {
    throw new Error("No ConfigContext found. Did you forget a ConfigProvider?");
  }
  return ctx;
}

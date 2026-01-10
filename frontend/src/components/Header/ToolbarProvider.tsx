import { Alert, Box, CircularProgress } from "@mui/material";
import { createContext, useContext } from "react";
import { ConfigResponse, useConfig } from "../../api/config";
import { useArrayQueryParam, useGlobalParam } from "../useSearchParam";
import { DateRangeKey, DateRanges } from "./DateRangeSelection";

export interface ToolbarContextType {
  investmentFilter: string[];
  setInvestmentFilter: (i: string[]) => void;
  targetCurrency: string;
  setTargetCurrency: (c: string) => void;
  dateRange?: DateRangeKey;
  setDateRange: (x: DateRangeKey) => void;
  config: ConfigResponse;
}

const ToolbarContext = createContext<ToolbarContextType | undefined>(undefined);

interface ToolbarProviderProps {
  children?: React.ReactNode;
}

export function ToolbarProvider({ children }: ToolbarProviderProps) {
  const { isPending, error, data: config } = useConfig();

  const [investmentFilter, setInvestmentFilter] = useArrayQueryParam(useGlobalParam("investments"));

  const [_targetCurrency, _setTargetCurrency] = useGlobalParam("currency");
  const targetCurrency = _targetCurrency ?? config?.operatingCurrencies[0] ?? "USD";
  const setTargetCurrency = (c: string) => _setTargetCurrency(c !== config?.operatingCurrencies[0] ? c : undefined);

  const [_dateRange, _setDateRange] = useGlobalParam("time");
  const dateRange = findDateRange(typeof _dateRange === "number" ? String(_dateRange) : _dateRange);
  const setDateRange = (x: DateRangeKey) => _setDateRange(x === "MAX" ? undefined : DateRanges[x]);

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

  return (
    <ToolbarContext.Provider
      value={{
        investmentFilter,
        setInvestmentFilter,
        targetCurrency,
        setTargetCurrency,
        dateRange,
        setDateRange,
        config,
      }}
    >
      {children}
    </ToolbarContext.Provider>
  );
}

export function useToolbarContext(): ToolbarContextType {
  const ctx = useContext(ToolbarContext);
  if (ctx === undefined) {
    throw new Error("No ToolbarContext found. Did you forget a Provider?");
  }
  return ctx;
}

function findDateRange(time: string | undefined): DateRangeKey | undefined {
  if (!time) {
    return "MAX";
  }
  for (const [key, val] of Object.entries(DateRanges)) {
    if (val === time) {
      return key as DateRangeKey;
    }
  }
  return undefined;
}

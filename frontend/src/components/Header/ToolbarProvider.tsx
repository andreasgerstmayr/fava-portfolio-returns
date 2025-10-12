import { Alert, Box, CircularProgress } from "@mui/material";
import { createContext, useContext } from "react";
import { StringParam, useQueryParam, withDefault } from "use-query-params";
import { ConfigResponse, useConfig } from "../../api/config";
import { CommaArrayParam } from "../query_params";
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
const InvestmentsFilterParam = withDefault(CommaArrayParam, []);

interface ToolbarProviderProps {
  children?: React.ReactNode;
}

export function ToolbarProvider({ children }: ToolbarProviderProps) {
  const { isPending, error, data: config } = useConfig();

  const [_investmentFilter, _setInvestmentFilter] = useQueryParam("investments", InvestmentsFilterParam);
  const investmentFilter = _investmentFilter.filter((i) => i !== null) as string[];
  const setInvestmentFilter = (i: string[]) => _setInvestmentFilter(i.length > 0 ? i : undefined);

  const [_targetCurrency, _setTargetCurrency] = useQueryParam("currency", StringParam);
  const targetCurrency = _targetCurrency ?? config?.operatingCurrencies[0] ?? "USD";
  const setTargetCurrency = (c: string) => _setTargetCurrency(c !== config?.operatingCurrencies[0] ? c : undefined);

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
        dateRange: getDateRange(),
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

function getDateRange(): DateRangeKey | undefined {
  const params = new URLSearchParams(location.search);
  const time = params.get("time");

  if (time === null) {
    return "MAX";
  }
  for (const [key, val] of Object.entries(DateRanges)) {
    if (val === time) {
      return key as DateRangeKey;
    }
  }
  return undefined;
}

function setDateRange(dateRange: DateRangeKey) {
  const url = new URL(location.href);
  if (dateRange === "MAX") {
    url.searchParams.delete("time");
  } else {
    url.searchParams.set("time", DateRanges[dateRange]);
  }
  location.href = url.toString();
}

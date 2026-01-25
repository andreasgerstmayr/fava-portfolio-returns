import { createContext, useContext } from "react";
import { useArrayQueryParam, useGlobalParam } from "../useSearchParam";
import { useConfigContext } from "./ConfigProvider";
import { DateRangeKey, DateRanges } from "./DateRangeSelection";

export interface ToolbarContextType {
  investmentFilter: string[];
  setInvestmentFilter: (i: string[]) => void;
  targetCurrency: string;
  setTargetCurrency: (c: string) => void;
  dateRange?: DateRangeKey;
  setDateRange: (x: DateRangeKey) => void;
}

const ToolbarContext = createContext<ToolbarContextType | undefined>(undefined);

interface ToolbarProviderProps {
  children?: React.ReactNode;
}

export function ToolbarProvider({ children }: ToolbarProviderProps) {
  const { config } = useConfigContext();

  const [investmentFilter, setInvestmentFilter] = useArrayQueryParam(useGlobalParam("investments"));

  const [_targetCurrency, _setTargetCurrency] = useGlobalParam("currency");
  const targetCurrency = _targetCurrency ?? config?.operatingCurrencies[0] ?? "USD";
  const setTargetCurrency = (c: string) => _setTargetCurrency(c !== config?.operatingCurrencies[0] ? c : undefined);

  const [_dateRange, _setDateRange] = useGlobalParam("time");
  const dateRange = findDateRange(typeof _dateRange === "number" ? String(_dateRange) : _dateRange);
  const setDateRange = (x: DateRangeKey) => _setDateRange(x === "MAX" ? undefined : DateRanges[x]);

  return (
    <ToolbarContext.Provider
      value={{
        investmentFilter,
        setInvestmentFilter,
        targetCurrency,
        setTargetCurrency,
        dateRange,
        setDateRange,
      }}
    >
      {children}
    </ToolbarContext.Provider>
  );
}

export function useToolbarContext(): ToolbarContextType {
  const ctx = useContext(ToolbarContext);
  if (ctx === undefined) {
    throw new Error("No ToolbarContext found. Did you forget a ToolbarProvider?");
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

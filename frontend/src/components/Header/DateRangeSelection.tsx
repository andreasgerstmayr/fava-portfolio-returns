import { ToggleButton, ToggleButtonGroup } from "@mui/material";
import moment from "moment";
import { useToolbarContext } from "./ToolbarProvider";

export const DateRanges = {
  "3M": moment().subtract(3, "months").format("YYYY-MM-DD") + " - day",
  "6M": moment().subtract(6, "months").format("YYYY-MM-DD") + " - day",
  YTD: "year - day",
  "1Y": moment().subtract(1, "years").format("YYYY-MM-DD") + " - day",
  "3Y": moment().subtract(3, "years").format("YYYY-MM-DD") + " - day",
  "5Y": moment().subtract(5, "years").format("YYYY-MM-DD") + " - day",
  MAX: undefined,
};
export type DateRangeKey = keyof typeof DateRanges;

export function DateRangeSelection() {
  const { dateRange, setDateRange } = useToolbarContext();

  return (
    <ToggleButtonGroup value={dateRange} onChange={(_e, value) => setDateRange(value)} exclusive>
      {Object.keys(DateRanges).map((timeRange) => (
        <ToggleButton key={timeRange} value={timeRange}>
          {timeRange}
        </ToggleButton>
      ))}
    </ToggleButtonGroup>
  );
}

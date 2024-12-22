import { MenuItem, Select } from "@mui/material";

export const ReturnsMethods = {
  simple: { label: "Returns", help: "Return compares the cost value with the market value." },
  irr: {
    label: "Internal Rate of Returns",
    help:
      "Internal Rate of Return (IRR) accounts for the timing and magnitude of cash flows.\n" +
      "This method is recommended when you are in control of the cash flows.",
  },
  twr: {
    label: "Time-Weighted Rate of Return",
    help:
      "Time-Weighted Return (TWR) eliminates the effects of cash flows.\n" +
      "This method is recommended for comparing two funds or portfolios.",
  },
};

export type ReturnsMethod = keyof typeof ReturnsMethods;

interface ReturnsMethodSelectionProps<T> {
  options: T[];
  method: T;
  setMethod: (x: T) => void;
}

export function ReturnsMethodSelection<T extends ReturnsMethod>({
  options,
  method,
  setMethod,
}: ReturnsMethodSelectionProps<T>) {
  return (
    <Select value={method} onChange={(e) => setMethod(e.target.value as T)} displayEmpty size="small">
      {options.map((option) => (
        <MenuItem key={option} value={option}>
          {ReturnsMethods[option].label}
        </MenuItem>
      ))}
    </Select>
  );
}

import { MenuItem, Select } from "@mui/material";

export const ReturnsMethods = {
  simple: { label: "Returns" },
  irr: {
    label: "Internal Rate of Return",
  },
  mdm: {
    label: "Modified Dietz Method",
  },
  twr: {
    label: "Time-Weighted Rate of Return",
  },
  monetary: { label: "Monetary Returns" },
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

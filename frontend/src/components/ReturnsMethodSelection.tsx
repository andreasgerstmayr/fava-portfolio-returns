import { MenuItem, Select } from "@mui/material";
import { useTranslation } from "react-i18next";

export function useReturnsMethods() {
  const { t } = useTranslation();
  return {
    simple: { label: t("Returns") },
    irr: {
      label: t("Internal Rate of Return"),
    },
    mdm: {
      label: t("Modified Dietz Method"),
    },
    twr: {
      label: t("Time-Weighted Rate of Return"),
    },
    pnl: { label: t("Total Profit and Loss") },
  };
}

export type ReturnsMethod = keyof ReturnType<typeof useReturnsMethods>;

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
  const returnsMethods = useReturnsMethods();

  return (
    <Select value={method} onChange={(e) => setMethod(e.target.value as T)} displayEmpty size="small">
      {options.map((option) => (
        <MenuItem key={option} value={option}>
          {returnsMethods[option].label}
        </MenuItem>
      ))}
    </Select>
  );
}

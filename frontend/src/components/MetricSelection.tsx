import { MenuItem, Select } from "@mui/material";
import { useTranslation } from "react-i18next";

export function useMetricNames() {
  const { t } = useTranslation();
  return {
    returns: { label: t("Returns") },
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

export type MetricName = keyof ReturnType<typeof useMetricNames>;

interface MetricSelectionProps<T> {
  options: T[];
  value: T;
  setValue: (x: T) => void;
}

export function MetricSelection<T extends MetricName>({ options, value, setValue }: MetricSelectionProps<T>) {
  const metricNames = useMetricNames();

  return (
    <Select value={value} onChange={(e) => setValue(e.target.value as T)} displayEmpty size="small">
      {options.map((option) => (
        <MenuItem key={option} value={option}>
          {metricNames[option].label}
        </MenuItem>
      ))}
    </Select>
  );
}

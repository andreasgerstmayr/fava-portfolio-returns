import { MenuItem, Select } from "@mui/material";
import { useTranslation } from "react-i18next";

export type MetricName = keyof ReturnType<typeof useMetrics>;

export function useMetrics() {
  const { t } = useTranslation();
  return {
    returns: {
      label: t("Returns"),
      format: "percent",
      supportSeries: true,
    },
    irr: {
      label: t("Internal Rate of Return"),
      format: "percent",
      supportSeries: false,
    },
    mdm: {
      label: t("Modified Dietz Method"),
      format: "percent",
      supportSeries: false,
    },
    twr: {
      label: t("Time-Weighted Rate of Return"),
      format: "percent",
      supportSeries: true,
    },
    pnl: {
      label: t("Total Profit and Loss"),
      format: "currency",
      supportSeries: true,
    },
  };
}

export function useMetric(name: MetricName) {
  const metrics = useMetrics();
  return metrics[name];
}

interface MetricSelectionProps<T> {
  options: T[];
  value: T;
  setValue: (x: T) => void;
}

export function MetricSelection<T extends MetricName>({ options, value, setValue }: MetricSelectionProps<T>) {
  const metrics = useMetrics();

  return (
    <Select value={value} onChange={(e) => setValue(e.target.value as T)} displayEmpty size="small">
      {options.map((option) => (
        <MenuItem key={option} value={option}>
          {metrics[option].label}
        </MenuItem>
      ))}
    </Select>
  );
}

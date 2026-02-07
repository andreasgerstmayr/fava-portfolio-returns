import { MenuItem, Select } from "@mui/material";
import { useTranslation } from "react-i18next";

export type MetricName = keyof ReturnType<typeof useMetrics>;

export function useMetrics() {
  const { t } = useTranslation();
  return {
    returns: {
      label: t("Returns"),
      unit: "percent",
      supportSeries: true,
    },
    irr: {
      label: t("Internal Rate of Return"),
      unit: "percent",
      supportSeries: false,
    },
    mdm: {
      label: t("Modified Dietz Method"),
      unit: "percent",
      supportSeries: false,
    },
    twr: {
      label: t("Time-Weighted Rate of Return"),
      unit: "percent",
      supportSeries: true,
    },
    pnl: {
      label: t("Total Profit and Loss"),
      unit: "currency",
      supportSeries: true,
    },
    volatility: {
      label: t("Volatility"),
      unit: "percent",
      supportSeries: false,
    },
    mdd: {
      label: t("Maximum Drawdown"),
      unit: "percent",
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

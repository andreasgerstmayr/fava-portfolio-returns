import { useTheme } from "@mui/material/styles";
import { dispose, ECElementEvent, ECharts, EChartsOption, init } from "echarts";
import { CSSProperties, useEffect, useRef } from "react";
import { useConfigContext } from "./Header/ConfigProvider";
import { useResizeObserver } from "./hooks";

export interface EChartsSpec extends EChartsOption {
  onClick?: (params: ECElementEvent) => void;
}

interface EChartProps {
  height: CSSProperties["height"];
  option: EChartsSpec;
}

export function EChart({ height, option }: EChartProps) {
  const { config } = useConfigContext();
  const theme = useTheme();
  const ref = useRef<HTMLDivElement>(null);
  const chartRef = useRef<ECharts>(null);
  const rect = useResizeObserver(ref);
  const echartsTheme = theme.palette.mode === "dark" ? "dark" : undefined;

  function cleanup() {
    if (chartRef.current) {
      dispose(chartRef.current);
      chartRef.current = null;
    }
  }

  useEffect(() => {
    cleanup();
    if (!rect) {
      return;
    }

    const locale = config.language ? config.language.split("_")[0] : undefined;
    const chart = init(ref.current, echartsTheme, {
      width: rect.width,
      height: rect.height,
      locale,
    });
    const { onClick, ...optionCopy } = option;

    if (onClick) {
      chart.on("click", onClick);
    }

    if (echartsTheme == "dark" && optionCopy.backgroundColor === undefined) {
      optionCopy.backgroundColor = "transparent";
    }

    chart.setOption(optionCopy);
    chartRef.current = chart;

    return cleanup;
  }, [option, echartsTheme, rect, config.language]);

  useEffect(() => {
    if (chartRef.current && rect) {
      chartRef.current.resize({ width: rect.width, height: rect.height });
    }
  }, [rect]);

  return <div ref={ref} style={{ height }}></div>;
}

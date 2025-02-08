import * as echarts from "echarts";
import { CSSProperties, useEffect, useRef } from "react";

interface EChartProps {
  width?: CSSProperties["width"];
  height?: CSSProperties["height"];
  option: echarts.EChartsCoreOption;
}

export function EChart({ width, height, option }: EChartProps) {
  const ref = useRef<HTMLDivElement>(null);
  const chartRef = useRef<echarts.ECharts>();

  useEffect(() => {
    if (chartRef.current) {
      echarts.dispose(chartRef.current);
    }

    // use SVG renderer during HTML e2e tests, to compare snapshots
    const renderer = window.navigator.userAgent === "puppeteer-html" ? "svg" : undefined;
    const chart = echarts.init(ref.current, undefined, { renderer });
    if (option.onClick) {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      chart.on("click", (option as any).onClick);
      delete option.onClick;
    }

    // disable animations during e2e tests
    if (window.navigator.userAgent.includes("puppeteer")) {
      option.animation = false;
    }

    chart.setOption(option);
    chartRef.current = chart;
  }, [option]);

  return <div ref={ref} style={{ width, height }}></div>;
}

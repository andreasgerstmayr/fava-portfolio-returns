import * as echarts from "echarts";
import { getCurrencyFormatter } from "./utils";

export function ProfitAndLossChart(
    elem: HTMLElement,
    chartOptions: {
        currency: string;
        data: any;
        minDate: string;
        maxDate: string;
    },
) {
    const absoluteCheckbox = elem.querySelector("input") as HTMLInputElement;
    const chartDom = elem.querySelector(".chart") as HTMLElement;
    const renderer = window.navigator.userAgent === "puppeteer" ? "svg" : undefined;
    const chart = echarts.init(chartDom, undefined, { renderer });
    const currencyFormatter = getCurrencyFormatter(chartOptions.currency);
    const percentageFormatter = new Intl.NumberFormat(undefined, { style: "percent" }).format as (value: any) => string;

    const renderChart = (absolute: boolean) => {
        const option: echarts.EChartsOption = {
            title: {
                left: "center",
                text: "Profit and Loss",
            },
            tooltip: {
                trigger: "axis",
                valueFormatter: absolute ? currencyFormatter : percentageFormatter,
            },
            xAxis: {
                type: "time",
                min: chartOptions.minDate,
                max: chartOptions.maxDate,
            },
            yAxis: {
                type: "value",
                axisLabel: {
                    formatter: absolute ? currencyFormatter : percentageFormatter,
                },
            },
            series: [
                {
                    type: "line",
                    data: chartOptions.data[absolute ? "value" : "value_pct"],
                },
            ],
        };
        chart.setOption(option);
    };

    absoluteCheckbox.addEventListener("click", (e) => {
        const absolute = (e.target as HTMLInputElement).checked;
        renderChart(absolute);
    });
    renderChart(true);
}

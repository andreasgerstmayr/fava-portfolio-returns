import * as echarts from "echarts";
import { getCurrencyFormatter } from "./utils";

export const CumValueChart = (
    elem: HTMLElement,
    chartOptions: {
        currency: string;
        data: any;
        minDate: string;
        maxDate: string;
    }
) => {
    const amortizedCheckbox = elem.querySelector("input") as HTMLInputElement;
    const chartDom = elem.querySelector(".chart") as HTMLElement;
    const chart = echarts.init(chartDom);
    const currencyFormatter = getCurrencyFormatter(chartOptions.currency);

    const renderChart = (amortized: boolean) => {
        const option: echarts.EChartsOption = {
            title: {
                left: "center",
                text: "Cumulative Value",
            },
            tooltip: {
                trigger: "axis",
                valueFormatter: currencyFormatter,
            },
            legend: {
                bottom: 0,
            },
            xAxis: {
                type: "time",
                min: chartOptions.minDate,
                max: chartOptions.maxDate,
            },
            yAxis: {
                type: "value",
                axisLabel: {
                    formatter: currencyFormatter,
                },
            },
            series: [
                {
                    type: "line",
                    name: amortized ? "Amortized value from flows" : "Value from flows",
                    showSymbol: false,
                    data: chartOptions.data[amortized ? "gamounts" : "amounts"],
                },
                {
                    type: "line",
                    name: "Market value",
                    data: chartOptions.data["value"],
                },
            ],
        };
        chart.setOption(option);
    };

    amortizedCheckbox.addEventListener("click", (e) => {
        const amortized = (e.target as HTMLInputElement).checked;
        renderChart(amortized);
    });
    renderChart(false);
};

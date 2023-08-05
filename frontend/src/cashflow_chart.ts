import * as echarts from "echarts";
import { getCurrencyFormatter } from "./utils";

export const CashflowChart = (
    elem: HTMLElement,
    chartOptions: {
        currency: string;
        data: any;
        minDate: string;
        maxDate: string;
    }
) => {
    const logCheckbox = elem.querySelector("input") as HTMLInputElement;
    const chartDom = elem.querySelector(".chart") as HTMLElement;
    const chart = echarts.init(chartDom);
    const currencyFormatter = getCurrencyFormatter(chartOptions.currency);

    const renderChart = (logarithmic: boolean) => {
        const option: echarts.EChartsOption = {
            title: {
                left: "center",
                text: logarithmic ? "log(Cash Flows)" : "Cash Flows",
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
                min: new Date(chartOptions.minDate),
                max: new Date(chartOptions.maxDate),
            },
            yAxis: {
                type: (logarithmic ? "log" : "value") as any,
                axisLabel: {
                    formatter: currencyFormatter,
                },
            },
            series: [
                {
                    type: "bar",
                    name: "Excl. dividends",
                    data: chartOptions.data["exdiv"],
                    barWidth: 2,
                },
                {
                    type: "bar",
                    name: "Dividends",
                    data: chartOptions.data["div"],
                    barWidth: 2,
                },
            ],
        };
        chart.setOption(option);
    };

    logCheckbox.addEventListener("click", (e) => {
        const logarithmic = (e.target as HTMLInputElement).checked;
        renderChart(logarithmic);
    });
    renderChart(true);
};

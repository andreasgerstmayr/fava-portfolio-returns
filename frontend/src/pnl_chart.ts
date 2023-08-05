import * as echarts from "echarts";
import { getCurrencyFormatter } from "./utils";

export function ProfitAndLossChart(
    elem: HTMLElement,
    chartOptions: {
        currency: string;
        data: any;
        minDate: string;
        maxDate: string;
    }
) {
    const chart = echarts.init(elem);
    const currencyFormatter = getCurrencyFormatter(chartOptions.currency);

    const option: echarts.EChartsOption = {
        title: {
            left: "center",
            text: "Profit and Loss",
        },
        tooltip: {
            trigger: "axis",
            valueFormatter: currencyFormatter,
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
                data: chartOptions.data["value"],
            },
        ],
    };
    chart.setOption(option);
}

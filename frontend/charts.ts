import * as echarts from "echarts";

type SeriesItem = [any, any];
type ChartData = { [k: string]: SeriesItem[] };

function getCurrencyFormatter(currency: string) {
  const currencyFormat = new Intl.NumberFormat(undefined, {
    style: "currency",
    currency: currency,
  });
  return (value: any) => {
    return currencyFormat.format(value);
  };
}

export function cashflowChart(elementId: string, currency: string, data: ChartData, logarithmic: boolean = false) {
  const chartDom = document.getElementById(elementId);
  const chart = echarts.init(chartDom);
  const currencyFormatter = getCurrencyFormatter(currency);

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
      splitNumber: 8,
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
        data: data["exdiv"],
      },
      {
        type: "bar",
        name: "Dividends",
        data: data["div"],
      },
    ],
  };
  chart.setOption(option);
}

export function cumValueChart(elementId: string, currency: string, data: ChartData) {
  const chartDom = document.getElementById(elementId);
  const chart = echarts.init(chartDom);
  const currencyFormatter = getCurrencyFormatter(currency);

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
      splitNumber: 8,
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
        name: "Amortized value from flows",
        showSymbol: false,
        data: data["gamounts"],
      },
      {
        type: "line",
        name: "Market value",
        data: data["value"],
      },
    ],
  };
  chart.setOption(option);
}

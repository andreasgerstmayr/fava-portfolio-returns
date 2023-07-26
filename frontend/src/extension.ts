import * as echarts from "echarts";

function getCurrencyFormatter(currency: string) {
  const currencyFormat = new Intl.NumberFormat(undefined, {
    style: "currency",
    currency,
  });
  return (value: any) => {
    return currencyFormat.format(value);
  };
}

export function cashflowChart(chartOptions: {
  elementId: string;
  currency: string;
  data: any;
  minDate: string;
  maxDate: string;
  logarithmic?: boolean;
}) {
  const chartDom = document.getElementById(chartOptions.elementId);
  const chart = echarts.init(chartDom);
  const currencyFormatter = getCurrencyFormatter(chartOptions.currency);

  const option: echarts.EChartsOption = {
    title: {
      left: "center",
      text: chartOptions.logarithmic ? "log(Cash Flows)" : "Cash Flows",
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
      type: (chartOptions.logarithmic ? "log" : "value") as any,
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
}

export function cumValueChart(chartOptions: {
  elementId: string;
  currency: string;
  data: any;
  minDate: string;
  maxDate: string;
}) {
  const chartDom = document.getElementById(chartOptions.elementId);
  const chart = echarts.init(chartDom);
  const currencyFormatter = getCurrencyFormatter(chartOptions.currency);

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
        name: "Amortized value from flows",
        showSymbol: false,
        data: chartOptions.data["gamounts"],
      },
      {
        type: "line",
        name: "Market value",
        data: chartOptions.data["value"],
      },
    ],
  };
  chart.setOption(option);
}

export default {
  onExtensionPageLoad() {
    const reportJSON = (document.querySelector("#favaPortfolioReturnsReportData") as HTMLScriptElement)?.text;
    if (!reportJSON) return;

    const report = JSON.parse(reportJSON);
    cashflowChart({
      elementId: "cashflow-chart",
      currency: report["target_currency"],
      data: report["plots"]["cashflows"],
      minDate: report["plots"]["min_date"],
      maxDate: report["plots"]["max_date"],
    });
    cashflowChart({
      elementId: "cashflow-log-chart",
      currency: report["target_currency"],
      data: report["plots"]["cashflows"],
      minDate: report["plots"]["min_date"],
      maxDate: report["plots"]["max_date"],
      logarithmic: true,
    });
    cumValueChart({
      elementId: "cumvalue-chart",
      currency: report["target_currency"],
      data: report["plots"]["cumvalue"],
      minDate: report["plots"]["min_date"],
      maxDate: report["plots"]["max_date"],
    });
  },
};

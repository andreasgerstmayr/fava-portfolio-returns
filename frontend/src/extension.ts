import { CashflowChart } from "./cashflow_chart";
import { CumValueChart } from "./cumvalue_chart";
import { ProfitAndLossChart } from "./pnl_chart";

function renderCharts(report) {
    ProfitAndLossChart(document.querySelector("#pnl-chart")!, {
        currency: report["target_currency"],
        data: report["plots"]["pnl"],
        minDate: report["plots"]["min_date"],
        maxDate: report["plots"]["max_date"],
    });
    CumValueChart(document.querySelector("#cumvalue-chart")!, {
        currency: report["target_currency"],
        data: report["plots"]["cumvalue"],
        minDate: report["plots"]["min_date"],
        maxDate: report["plots"]["max_date"],
    });
    CashflowChart(document.querySelector("#cashflow-chart")!, {
        currency: report["target_currency"],
        data: report["plots"]["cashflows"],
        minDate: report["plots"]["min_date"],
        maxDate: report["plots"]["max_date"],
    });
}

export default {
    onExtensionPageLoad() {
        const reportJSON = (document.querySelector("#favaPortfolioReturnsReportData") as HTMLScriptElement)?.text;
        if (!reportJSON) return;

        const report = JSON.parse(reportJSON);
        renderCharts(report);
    },
};

import { Alert, Box } from "@mui/material";
import { createEnumParam, useQueryParam, withDefault } from "use-query-params";
import { useCompare } from "../api/compare";
import { Dashboard, DashboardRow, Panel } from "../components/Dashboard";
import { EChart } from "../components/EChart";
import { useToolbarContext } from "../components/Header/ToolbarProvider";
import { InvestmentsSelection } from "../components/InvestmentsSelection";
import { Loading } from "../components/Loading";
import { ReturnsMethodSelection } from "../components/ReturnsMethodSelection";
import { percentFormatter } from "../components/format";
import { CommaArrayParam } from "../components/query_params";

const ReturnsMethodEnum = createEnumParam(["simple", "twr"]);
const ReturnsMethodParam = withDefault(ReturnsMethodEnum, "simple" as const);
const InvestmentsParam = withDefault(CommaArrayParam, []);

export function Performance() {
  const [method, setMethod] = useQueryParam("method", ReturnsMethodParam);
  const [_investments, setInvestments] = useQueryParam("compareWith", InvestmentsParam);
  const investments = _investments.filter((i) => i !== null) as string[];

  return (
    <Dashboard>
      <DashboardRow>
        <Panel
          title="Performance"
          help={`The performance chart compares the relative performance of the currently selected investments (comprising a part of your portfolio filtered using the "Investments Filter") against single groups, accounts or commodities selected in the "Compare with" box below.`}
          topRightElem={<ReturnsMethodSelection options={["simple", "twr"]} method={method} setMethod={setMethod} />}
        >
          <PerformanceChart method={method} investments={investments} />
          <Box sx={{ display: "flex", justifyContent: "center", marginTop: 3 }}>
            <InvestmentsSelection
              label="Compare with"
              types={["Group", "Currency", "Account"]}
              investments={investments}
              setInvestments={setInvestments}
            />
          </Box>
        </Panel>
      </DashboardRow>
    </Dashboard>
  );
}

interface PerformanceChartProps {
  method: string;
  investments: string[];
}

function PerformanceChart({ method, investments }: PerformanceChartProps) {
  const { investmentFilter, targetCurrency } = useToolbarContext();
  const { isPending, error, data } = useCompare({
    investmentFilter,
    targetCurrency,
    method,
    compareWith: investments,
  });

  if (isPending) {
    return <Loading />;
  }
  if (error) {
    return <Alert severity="error">{error.message}</Alert>;
  }

  const option = {
    tooltip: {
      trigger: "axis",
      valueFormatter: percentFormatter,
    },
    legend: {
      top: 10,
    },
    grid: {
      left: 100,
    },
    xAxis: {
      type: "time",
    },
    yAxis: {
      type: "value",
      axisLabel: {
        formatter: percentFormatter,
      },
    },
    dataZoom: [
      {
        type: "slider",
        handleLabel: {
          show: true,
        },
      },
    ],
    series: data.series.map((serie) => ({
      type: "line",
      showSymbol: false,
      name: serie.name,
      data: serie.data,
    })),
  };

  return <EChart height="500px" option={option} />;
}

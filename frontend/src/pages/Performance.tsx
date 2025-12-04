import { Alert, Box, FormControlLabel, FormGroup, Switch, useTheme } from "@mui/material";
import { BooleanParam, createEnumParam, useQueryParam, withDefault } from "use-query-params";
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
  const [showBuySellPoints, setShowBuySellPoints] = useQueryParam("buySellPoints", BooleanParam);
  const investments = _investments.filter((i) => i !== null) as string[];

  return (
    <Dashboard>
      <DashboardRow>
        <Panel
          title="Performance"
          help={`The performance chart compares the relative performance of the currently selected investments (comprising a part of your portfolio filtered using the "Investments Filter") against single groups, accounts or commodities selected in the "Compare with" box below.`}
          topRightElem={<ReturnsMethodSelection options={["simple", "twr"]} method={method} setMethod={setMethod} />}
        >
          <PerformanceChart method={method} investments={investments} showBuySellPoints={!!showBuySellPoints} />
          <Box sx={{ display: "flex", justifyContent: "center", marginTop: 3 }}>
            <FormGroup>
              <FormControlLabel
                control={<Switch checked={!!showBuySellPoints} onChange={(_, value) => setShowBuySellPoints(value)} />}
                label="Show Buy/Sell Points"
              />
            </FormGroup>
          </Box>
          <Box sx={{ display: "flex", justifyContent: "center", marginTop: 3 }}>
            <InvestmentsSelection
              label="Compare with"
              types={["Group", "Account", "Currency"]}
              includeAllCurrencies
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
  showBuySellPoints: boolean;
}

function PerformanceChart({ method, investments, showBuySellPoints }: PerformanceChartProps) {
  const theme = useTheme();
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

  // Calculate dynamic symbol size based on relative transaction amount
  const calculateSymbolSize = (
    amount: number,
    portfolioValue: number,
    minAmount: number,
    maxAmount: number,
  ): number => {
    const absAmount = Math.abs(amount);

    // Handle edge case where all amounts are the same
    if (maxAmount === minAmount) {
      return 8; // Default to medium size
    }

    // Calculate linear position between min and max (0 to 1)
    const relativePosition = (absAmount - minAmount) / (maxAmount - minAmount);

    // Map to pixel size range: 4px (smallest) to 16px (largest)
    const size = 4 + relativePosition * 12;

    // Ensure size is within bounds
    return Math.min(Math.max(size, 4), 16);
  };

  // Generate mark point data
  const generateMarkPoints = (cashFlows: [string, number][], seriesData: [string, number][]) => {
    // Find minimum and maximum absolute amounts for relative scaling
    const absAmounts = cashFlows.map(([_, amount]) => Math.abs(amount));
    const minAmount = Math.min(...absAmounts);
    const maxAmount = Math.max(...absAmounts);

    // Convert series data to timestamp format for easier matching
    const seriesDataWithTimestamps: [number, number][] = seriesData.map(([dateStr, value]) => {
      const date = new Date(dateStr);
      return [date.getTime(), value];
    });

    return cashFlows.map(([dateStr, amount]) => {
      // Convert cash flow date string to timestamp
      const cashFlowDate = new Date(dateStr);
      const cashFlowTimestamp = cashFlowDate.getTime();

      // Find the closest series data point
      let closestYValue = 0;
      let minDiff = Infinity;

      for (const [timestamp, yValue] of seriesDataWithTimestamps) {
        const diff = Math.abs(timestamp - cashFlowTimestamp);
        if (diff < minDiff) {
          minDiff = diff;
          closestYValue = yValue;
        }
      }

      // Calculate relative size based on amount compared to min/max range
      const portfolioValue = closestYValue;
      const dynamicSize = calculateSymbolSize(amount, portfolioValue, minAmount, maxAmount);

      // For ECharts time axis with type "time", we can use timestamp
      return {
        coord: [cashFlowTimestamp, closestYValue], // Display point on the line
        value: amount,
        symbol: "circle",
        symbolSize: dynamicSize,
        itemStyle: {
          color: amount < 0 ? theme.pnl.profit : theme.pnl.loss,
        },
        label: {
          show: false,
        },
      };
    });
  };

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
      markPoint:
        showBuySellPoints && serie.cash_flows
          ? {
              data: generateMarkPoints(serie.cash_flows, serie.data),
              label: {
                show: false,
              },
            }
          : undefined,
    })),
  };

  return <EChart height="500px" option={option} />;
}

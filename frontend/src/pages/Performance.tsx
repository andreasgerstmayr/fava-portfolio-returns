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
const SymbolScalingEnum = createEnumParam(["linear", "logarithmic"]);
const SymbolScalingParam = withDefault(SymbolScalingEnum, "linear" as const);

export function Performance() {
  const [method, setMethod] = useQueryParam("method", ReturnsMethodParam);
  const [_investments, setInvestments] = useQueryParam("compareWith", InvestmentsParam);
  const [showBuySellPoints, setShowBuySellPoints] = useQueryParam("buySellPoints", BooleanParam);
  const [symbolScaling, setSymbolScaling] = useQueryParam("symbolScaling", SymbolScalingParam);
  const investments = _investments.filter((i) => i !== null) as string[];

  return (
    <Dashboard>
      <DashboardRow>
        <Panel
          title="Performance"
          help={`The performance chart compares the relative performance of the currently selected investments (comprising a part of your portfolio filtered using the "Investments Filter") against single groups, accounts or commodities selected in the "Compare with" box below.`}
          topRightElem={<ReturnsMethodSelection options={["simple", "twr"]} method={method} setMethod={setMethod} />}
        >
          <PerformanceChart
            method={method}
            investments={investments}
            showBuySellPoints={!!showBuySellPoints}
            symbolScaling={symbolScaling}
          />
          <Box sx={{ display: "flex", justifyContent: "center", marginTop: 3, gap: 4 }}>
            <FormGroup>
              <FormControlLabel
                control={<Switch checked={!!showBuySellPoints} onChange={(_, value) => setShowBuySellPoints(value)} />}
                label="Show Buy/Sell Points"
              />
            </FormGroup>
            {showBuySellPoints && (
              <FormGroup>
                <FormControlLabel
                  control={
                    <Switch
                      checked={symbolScaling === "logarithmic"}
                      onChange={(e, value) => setSymbolScaling(value ? "logarithmic" : "linear")}
                    />
                  }
                  label="Logarithmic Scaling"
                />
              </FormGroup>
            )}
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
  symbolScaling: "linear" | "logarithmic";
}

function PerformanceChart({ method, investments, showBuySellPoints, symbolScaling }: PerformanceChartProps) {
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
    scalingMode: "linear" | "logarithmic" = "logarithmic",
  ): number => {
    const absAmount = Math.abs(amount);

    // Handle edge case where all amounts are the same
    if (maxAmount === minAmount) {
      return 8; // Default to medium size
    }

    let relativePosition: number;

    if (scalingMode === "logarithmic") {
      // Prevent taking log of zero or negative numbers
      if (absAmount <= 0 || minAmount <= 0) {
        return 4; // Minimum size for non-positive amounts
      }

      // Use logarithmic scaling to compress range while maintaining relative proportions
      const logMin = Math.log(minAmount);
      const logMax = Math.log(maxAmount);
      const logAmount = Math.log(absAmount);

      // Calculate relative position in logarithmic space
      relativePosition = (logAmount - logMin) / (logMax - logMin);
    } else {
      // Original linear scaling logic
      relativePosition = (absAmount - minAmount) / (maxAmount - minAmount);
    }

    // Map to pixel size range: 4px (minimum) to 16px (maximum)
    const size = 4 + relativePosition * 12;

    // Ensure size is within bounds
    return Math.min(Math.max(size, 4), 16);
  };

  // Generate mark point data
  const generateMarkPoints = (
    cashFlows: [string, number][],
    seriesData: [string, number][],
    scalingMode: "linear" | "logarithmic",
  ) => {
    // Find minimum and maximum absolute amounts for relative scaling
    const absAmounts = cashFlows.map(([_, amount]) => Math.abs(amount));
    const minAmount = Math.min(...absAmounts);
    const maxAmount = Math.max(...absAmounts);

    // Create a map for fast date lookup - using the exact format from seriesData
    const seriesDataMap = new Map<string, { value: number; originalDateStr: string }>();
    for (const [dateStr, value] of seriesData) {
      // Normalize to YYYY-MM-DD format for matching
      const date = new Date(dateStr);
      const normalizedDateStr = date.toISOString().split("T")[0];
      seriesDataMap.set(normalizedDateStr, { value, originalDateStr: dateStr });
    }

    return cashFlows
      .map(([dateStr, amount]) => {
        // Normalize cash flow date to YYYY-MM-DD format for matching
        const cashFlowDate = new Date(dateStr);
        const normalizedDateStr = cashFlowDate.toISOString().split("T")[0];

        // Find matching series data
        const match = seriesDataMap.get(normalizedDateStr);

        if (!match) {
          // Skip this point if no matching series data exists
          return null;
        }

        // Use the exact same date string format as the series data for perfect alignment
        const yValue = match.value;

        // Calculate relative size based on amount compared to min/max range
        const portfolioValue = yValue;
        const dynamicSize = calculateSymbolSize(amount, portfolioValue, minAmount, maxAmount, scalingMode);

        // Use the original date string from series data to ensure perfect alignment
        return {
          coord: [match.originalDateStr, yValue], // Use the same date string format as series data
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
      })
      .filter((point): point is NonNullable<typeof point> => point !== null);
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
              data: generateMarkPoints(serie.cash_flows, serie.data, symbolScaling),
              label: {
                show: false,
              },
            }
          : undefined,
    })),
  };

  return <EChart height="500px" option={option} />;
}

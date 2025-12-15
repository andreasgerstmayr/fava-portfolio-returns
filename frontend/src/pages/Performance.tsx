import {
  Alert,
  Box,
  FormControl,
  FormControlLabel,
  FormGroup,
  FormLabel,
  Switch,
  Theme,
  useTheme,
} from "@mui/material";
import { EChartsOption } from "echarts";
import { BooleanParam, createEnumParam, useQueryParam, withDefault } from "use-query-params";
import { NamedSeries, useCompare } from "../api/compare";
import { Dashboard, DashboardRow, Panel } from "../components/Dashboard";
import { EChart } from "../components/EChart";
import { useToolbarContext } from "../components/Header/ToolbarProvider";
import { InvestmentsSelection } from "../components/InvestmentsSelection";
import { Loading } from "../components/Loading";
import { ReturnsMethodSelection } from "../components/ReturnsMethodSelection";
import { anyFormatter, percentFormatter } from "../components/format";
import { CommaArrayParam } from "../components/query_params";

const ReturnsMethodEnum = createEnumParam(["simple", "twr"]);
const ReturnsMethodParam = withDefault(ReturnsMethodEnum, "simple" as const);
const InvestmentsParam = withDefault(CommaArrayParam, []);
const BuySellPoints = withDefault(BooleanParam, false);
const SymbolScalingEnum = createEnumParam(["linear", "logarithmic"]);
const SymbolScalingParam = withDefault(SymbolScalingEnum, "linear" as const);

export function Performance() {
  const [method, setMethod] = useQueryParam("method", ReturnsMethodParam);
  const [_investments, setInvestments] = useQueryParam("compareWith", InvestmentsParam);
  const [showBuySellPoints, setShowBuySellPoints] = useQueryParam("buySellPoints", BuySellPoints);
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
            showBuySellPoints={showBuySellPoints}
            symbolScaling={symbolScaling}
          />
          <Box sx={{ display: "flex", justifyContent: "center", marginTop: 3 }}>
            <InvestmentsSelection
              label="Compare with"
              types={["Group", "Account", "Currency"]}
              includeAllCurrencies
              investments={investments}
              setInvestments={setInvestments}
            />
          </Box>
          <Box sx={{ display: "flex", justifyContent: "center", marginTop: 3 }}>
            <FormControl component="fieldset" variant="outlined">
              <FormLabel component="legend">Buy/Sell points</FormLabel>
              <FormGroup>
                <FormControlLabel
                  label="Show"
                  control={<Switch checked={showBuySellPoints} onChange={(_, value) => setShowBuySellPoints(value)} />}
                />
                  <FormControlLabel
                    label="Logarithmic Scaling"
                    control={
                      <Switch
                        checked={symbolScaling === "logarithmic"}
                        disabled={!showBuySellPoints}
                        onChange={(e, value) => setSymbolScaling(value ? "logarithmic" : "linear")}
                      />
                    }
                  />
              </FormGroup>
            </FormControl>
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

  const option: EChartsOption = {
    tooltip: {
      trigger: "axis",
      valueFormatter: anyFormatter(percentFormatter),
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
      markPoint: showBuySellPoints
        ? {
            data: generateMarkPoints(theme, serie, symbolScaling),
            label: {
              show: false,
            },
          }
        : undefined,
    })),
  };

  return <EChart height="500px" option={option} />;
}

const [minSymbolSize, maxSymbolSize] = [8, 16];

function safeLog(x: number) {
  return x > 0 ? Math.log(x) : 0;
}

// Calculate dynamic symbol size based on relative transaction amount
function calculateSymbolSize(
  amount: number,
  minAmount: number,
  maxAmount: number,
  scalingMode: "linear" | "logarithmic",
): number {
  // catch divison by zero
  if (maxAmount - minAmount === 0) {
    return minSymbolSize + (maxSymbolSize - minSymbolSize) / 2;
  }

  // apply linear/log scale of absAmount from range [minAmount,maxAmount] to a value from range [minSymbolSize,maxSymbolSize]
  let rel: number;
  switch (scalingMode) {
    case "linear":
      rel = (amount - minAmount) / (maxAmount - minAmount);
      break;
    case "logarithmic":
      rel = (safeLog(amount) - safeLog(minAmount)) / (safeLog(maxAmount) - safeLog(minAmount));
      break;
  }
  return minSymbolSize + (maxSymbolSize - minSymbolSize) * rel;
}

// Generate mark point data
function generateMarkPoints(theme: Theme, serie: NamedSeries, scalingMode: "linear" | "logarithmic") {
  // Find minimum and maximum absolute amounts for relative scaling
  const absAmounts = serie.cashFlows.map(([_, amount]) => Math.abs(amount));
  const minAmount = Math.min(...absAmounts);
  const maxAmount = Math.max(...absAmounts);

  // Create a map for fast date lookup
  const seriesDataMap = new Map<string, number>();
  for (const [dateStr, value] of serie.data) {
    seriesDataMap.set(dateStr, value);
  }

  return serie.cashFlows
    .map(([dateStr, amount]) => {
      // Find matching series data
      const yValue = seriesDataMap.get(dateStr);

      if (!yValue) {
        // Skip this point if no matching series data exists
        return null;
      }

      // Calculate relative size based on amount compared to min/max range
      const dynamicSize = calculateSymbolSize(Math.abs(amount), minAmount, maxAmount, scalingMode);

      return {
        name: dateStr,
        coord: [dateStr, yValue],
        value: amount,
        symbol: "triangle",
        symbolSize: dynamicSize,
        symbolRotate: amount <= 0 ? 0 : 180,
        itemStyle: {
          color: amount <= 0 ? theme.pnl.profit : theme.pnl.loss,
        },
      };
    })
    .filter((point) => point !== null);
}

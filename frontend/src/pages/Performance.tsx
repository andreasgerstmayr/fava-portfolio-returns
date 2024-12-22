import { Alert, Box } from "@mui/material";
import { createEnumParam, DelimitedArrayParam, useQueryParam, withDefault } from "use-query-params";
import { ConfigResponse } from "../api/config";
import { Series, useMultiSeries } from "../api/series";
import { Dashboard, DashboardRow, Panel } from "../components/Dashboard";
import { EChart } from "../components/EChart";
import { useToolbarContext } from "../components/Header/ToolbarProvider";
import { InvestmentsSelection } from "../components/InvestmentsSelection";
import { Loading } from "../components/Loading";
import { ReturnsMethods, ReturnsMethodSelection } from "../components/ReturnsMethodSelection";

const ReturnsMethodEnum = createEnumParam(["simple", "twr"]);
const ReturnsMethodParam = withDefault(ReturnsMethodEnum, "simple" as const);
const InvestmentsParam = withDefault(DelimitedArrayParam, [] as string[]);

export function Performance() {
  const [method, setMethod] = useQueryParam("method", ReturnsMethodParam);
  const [_investments, setInvestments] = useQueryParam("compareInvestments", InvestmentsParam);
  const investments = _investments.filter((i) => i !== null) as string[];

  return (
    <Dashboard>
      <DashboardRow>
        <Panel
          title="Performance"
          help={`The performance chart allows comparing the relative performance of the currently selected investments with other groups and commodities.\n${ReturnsMethods[method].help}`}
          topRightElem={<ReturnsMethodSelection options={["simple", "twr"]} method={method} setMethod={setMethod} />}
        >
          <PerformanceChart method={method} investments={investments} />
          <Box sx={{ display: "flex", justifyContent: "center", marginTop: 3 }}>
            <InvestmentsSelection
              label="Compare with"
              types={["Group", "Currency"]}
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

interface ChartSeries {
  name: string;
  data: Series;
  isPercentage: boolean;
}

function PerformanceChart({ method, investments }: PerformanceChartProps) {
  const { investmentFilter, targetCurrency, config } = useToolbarContext();

  const groups: ConfigResponse["investments"]["groups"] = [];
  for (const group of config.investments.groups) {
    if (investments.includes(group.id)) {
      groups.push(group);
    }
  }
  const currencies: ConfigResponse["investments"]["currencies"] = [];
  for (const currency of config.investments.currencies) {
    if (investments.includes(currency.id)) {
      currencies.push(currency);
    }
  }

  const { isPending, error, data } = useMultiSeries([
    {
      investmentFilter,
      targetCurrency,
      series: [`returns_${method}_series`, ...currencies.map((currency) => `price_${currency.currency}`)],
    },
    ...groups.map((group) => ({
      investmentFilter: [group.id],
      targetCurrency,
      series: [`returns_${method}_series`],
    })),
  ]);

  if (isPending) {
    return <Loading />;
  }
  if (error) {
    return <Alert severity="error">{error.message}</Alert>;
  }

  const percentFormatter = new Intl.NumberFormat(undefined, {
    style: "percent",
    maximumFractionDigits: 2,
  }).format;
  const signedPercentFormatter = new Intl.NumberFormat(undefined, {
    style: "percent",
    maximumFractionDigits: 2,
    signDisplay: "exceptZero",
  }).format;

  const series: ChartSeries[] = [
    {
      name: "Returns",
      data: data[0]?.series[`returns_${method}_series`] ?? [],
      isPercentage: true,
    },
    ...groups.map((group, i) => ({
      name: `(GRP) ${group.name}`,
      data: data[i + 1]?.series[`returns_${method}_series`] ?? [],
      isPercentage: true,
    })),
    ...currencies.map((currency) => ({
      name: currency.name,
      data: data[0]?.series[`price_${currency.currency}`] ?? [],
      isPercentage: false,
    })),
  ];

  try {
    normalizeSeries(series);
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
  } catch (error: any) {
    return <Alert severity="error">{error?.toString()}</Alert>;
  }

  const option = {
    tooltip: {
      trigger: "axis",
      valueFormatter: signedPercentFormatter,
    },
    legend: {
      bottom: 0,
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
    series: series.map((serie) => ({
      type: "line",
      showSymbol: false,
      name: serie.name,
      data: serie.data,
    })),
  };

  return <EChart height="400px" option={option} />;
}

/** find the first common date, cut off items before and normalize the rest */
function normalizeSeries(series: ChartSeries[]) {
  // ignore empty series
  series = series.filter((s) => s.data.length > 0);

  // less than 2 series, no need to normalize
  if (series.length < 2) return;

  // find first common date
  const first = series[0];
  const others = series.slice(1).map((s) => new Set(s.data.map(([date, _value]) => date)));
  const commonDate = first.data.find(([date, _value]) => others.every((s) => s.has(date)))?.[0];
  if (commonDate === undefined) {
    throw Error("No overlapping dates found for the selected series.");
  }

  for (const serie of series) {
    const idx = serie.data.findIndex(([date, _value]) => date === commonDate);
    if (idx === -1) continue; // cannot happen based on the code above

    const cut = serie.data.slice(idx);
    serie.data = serie.isPercentage ? normalizePercentageSeries(cut) : normalizePricesSeries(cut);
  }
}

/** to make returns series comparable, align series to start at 0% */
function normalizePercentageSeries(series: Series): Series {
  if (series.length === 0) {
    return [];
  }

  const [_date, firstValue] = series[0];
  if (firstValue == 0) {
    // already normalized
    return series;
  }

  return series.map(([date, value]) => [date, value - firstValue]);
}

/** to make prices comparable, calculate the relative performance */
function normalizePricesSeries(series: Series): Series {
  if (series.length === 0) {
    return [];
  }

  const [_date, firstValue] = series[0];
  if (firstValue == 0) {
    console.error("cannot normalize price series starting at 0", series);
    throw Error("cannot normalize price series starting at 0");
  }

  return series.map(([date, value]) => [date, value / firstValue - 1]);
}

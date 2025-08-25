import { Alert, FormControlLabel, FormGroup, Switch, useTheme } from "@mui/material";
import { Link } from "react-router";
import {
  BooleanParam,
  createEnumParam,
  StringParam,
  useQueryParam,
  useQueryParams,
  withDefault,
} from "use-query-params";
import { Investment, useInvestments } from "../api/investments";
import { Dashboard, DashboardRow, Panel } from "../components/Dashboard";
import { fixedPercentFormatter, numberFormatter } from "../components/format";
import { useToolbarContext } from "../components/Header/ToolbarProvider";
import { Loading } from "../components/Loading";
import { ReturnsMethods } from "../components/ReturnsMethodSelection";

export function Groups() {
  return (
    <Dashboard>
      <DashboardRow>
        <Panel title="Groups" help="Lists the groups defined in the beangrow configuration file.">
          <InvestmentsTable groupBy="group" />
        </Panel>
      </DashboardRow>
    </Dashboard>
  );
}

export function Investments() {
  return (
    <Dashboard>
      <DashboardRow>
        <Panel title="Investments" help="Lists the investments defined in the beangrow configuration file.">
          <InvestmentsTable groupBy="currency" />
        </Panel>
      </DashboardRow>
    </Dashboard>
  );
}

interface InvestmentsTableProps {
  groupBy: "group" | "currency";
}

const SortColumnParam = withDefault(StringParam, "name" as const);
const SortOrderEnum = createEnumParam(["asc", "desc"]);
const SortOrderParam = withDefault(SortOrderEnum, "asc" as const);
type SortableKeys = Exclude<keyof Investment, "units">;

export function InvestmentsTable({ groupBy }: InvestmentsTableProps) {
  const theme = useTheme();
  const { targetCurrency } = useToolbarContext();
  const { isPending, error, data } = useInvestments({ targetCurrency, groupBy });
  const [sort, setSort] = useQueryParams({
    sortColumn: SortColumnParam,
    sortOrder: SortOrderParam,
  });
  const [includeLiquidated, setIncludeLiquidated] = useQueryParam("liquidated", BooleanParam);

  const handleSortChange = (column: SortableKeys) => {
    if (sort.sortColumn === column) {
      setSort({ sortOrder: sort.sortOrder === "asc" ? "desc" : "asc" });
      return;
    }
    setSort({ sortColumn: column, sortOrder: "asc" });
  };

  if (isPending) {
    return <Loading />;
  }
  if (error) {
    return <Alert severity="error">{error.message}</Alert>;
  }

  if (Object.keys(data.investments).length === 0) {
    return (
      <Alert severity="info">
        No {groupBy === "group" ? "groups" : "investments"} defined in the beangrow configuration.
      </Alert>
    );
  }

  let investments = data.investments.toSorted((a, b) => {
    const x = a[sort.sortColumn as SortableKeys];
    const y = b[sort.sortColumn as SortableKeys];

    if (x === y) {
      return 0;
    }
    if (sort.sortOrder == "asc") {
      return x < y ? -1 : 1;
    } else {
      return x < y ? 1 : -1;
    }
  });
  if (!includeLiquidated) {
    investments = investments.filter((i) => i.marketValue > 0);
  }

  const sortParams = (column: SortableKeys) => ({
    "data-sort": "", // required For fava to display sort icon
    "data-order": sort.sortColumn === column ? sort.sortOrder : "", // required for Fava to display sort icon direction
    onClick: () => handleSortChange(column),
  });

  // use green for gains and red for losses
  const conditionalColor = (x: number) => (x >= 0 ? theme.pnl.profit : theme.pnl.loss);

  // cost value, market value and unrealized P/L will be zero once the investment is liquidated
  // realized P/L is zero if investment was never sold
  const nonZero = (x: number) => Math.abs(x) >= 0.01;

  const table = (
    <table>
      <thead>
        <tr>
          <th {...sortParams("name")}>Name</th>
          <th>Units</th>
          <th {...sortParams("costValue")}>Cost Value</th>
          <th {...sortParams("marketValue")}>Market Value</th>
          <th {...sortParams("realizedPnl")} title="Realized Profit and Loss: P&L from sold assets">
            Realized P/L
          </th>
          <th
            {...sortParams("unrealizedPnl")}
            title="Unrealized Profit and Loss: P&L from open positions (excluding fees)"
          >
            Unrealized P/L
          </th>
          <th {...sortParams("totalPnl")} title="Total Profit and Loss">
            Total P/L
          </th>
          <th {...sortParams("irr")} title={ReturnsMethods.irr.label}>
            IRR
          </th>
          <th {...sortParams("mdm")} title={ReturnsMethods.mdm.label}>
            MDM
          </th>
          <th {...sortParams("twr")} title={ReturnsMethods.twr.label}>
            TWR
          </th>
        </tr>
      </thead>
      <tbody>
        {investments.map((investment, i) => (
          <tr key={i}>
            <td>
              <Link
                to={`/portfolio?${new URLSearchParams({ investments: investment.id, currency: investment.currency })}`}
              >
                {investment.name}
              </Link>
            </td>
            <td className="num">
              {investment.units.map((unit, i) => (
                <span key={i}>
                  {numberFormatter(unit.number)} {unit.currency}
                  <br />
                </span>
              ))}
            </td>
            <td className="num">
              {nonZero(investment.costValue) && `${numberFormatter(investment.costValue)} ${investment.currency}`}
            </td>
            <td className="num">
              {nonZero(investment.marketValue) && `${numberFormatter(investment.marketValue)} ${investment.currency}`}
            </td>
            <td className="num" style={{ color: conditionalColor(investment.realizedPnl) }}>
              {nonZero(investment.realizedPnl) && `${numberFormatter(investment.realizedPnl)} ${investment.currency}`}
            </td>
            <td className="num" style={{ color: conditionalColor(investment.unrealizedPnl) }}>
              {nonZero(investment.unrealizedPnl) &&
                `${numberFormatter(investment.unrealizedPnl)} ${investment.currency}`}
            </td>
            <td className="num" style={{ color: conditionalColor(investment.totalPnl) }}>
              {numberFormatter(investment.totalPnl)} {investment.currency}
            </td>
            <td className="num" style={{ color: conditionalColor(investment.irr) }}>
              {fixedPercentFormatter(investment.irr)}
            </td>
            <td className="num" style={{ color: conditionalColor(investment.mdm) }}>
              {fixedPercentFormatter(investment.mdm)}
            </td>
            <td className="num" style={{ color: conditionalColor(investment.twr) }}>
              {fixedPercentFormatter(investment.twr)}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );

  return (
    <>
      {table}
      <FormGroup>
        <FormControlLabel
          control={<Switch value={includeLiquidated} onChange={(_, value) => setIncludeLiquidated(value)} />}
          label="Include liquidated investments"
        />
      </FormGroup>
    </>
  );
}

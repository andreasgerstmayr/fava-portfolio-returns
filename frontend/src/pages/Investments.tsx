import { Alert, FormControlLabel, FormGroup, Switch } from "@mui/material";
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
import {
  fixedPercentFormatter,
  NEGATIVE_NUMBER_COLOR,
  numberFormatter,
  POSITIVE_NUMBER_COLOR,
} from "../components/format";
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
  const percentFormatter = fixedPercentFormatter;

  const sortParams = (column: SortableKeys) => ({
    "data-sort": "", // required for fava to display sort icon
    "data-order": sort.sortColumn === column ? sort.sortOrder : "", // required for fava to display sort icon direction
    onClick: () => handleSortChange(column),
  });

  const numberColor = (x: number) => (x >= 0 ? POSITIVE_NUMBER_COLOR : NEGATIVE_NUMBER_COLOR);

  const table = (
    <table>
      <thead>
        <tr>
          <th {...sortParams("name")}>Name</th>
          <th>Units</th>
          <th {...sortParams("costValue")}>Cost Value</th>
          <th {...sortParams("marketValue")}>Market Value</th>
          <th {...sortParams("realizedPnl")} title="Realized Profit and Loss">
            Realized P/L
          </th>
          <th {...sortParams("unrealizedPnl")} title="Unrealized Profit and Loss">
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
              {investment.costValue != 0 && `${numberFormatter(investment.costValue)} ${investment.currency}`}
            </td>
            <td className="num">
              {investment.marketValue != 0 && `${numberFormatter(investment.marketValue)} ${investment.currency}`}
            </td>
            <td className="num" style={{ color: numberColor(investment.realizedPnl) }}>
              {Math.abs(investment.realizedPnl) >= 0.01 &&
                `${numberFormatter(investment.realizedPnl)} ${investment.currency}`}
            </td>
            <td className="num" style={{ color: numberColor(investment.unrealizedPnl) }}>
              {numberFormatter(investment.unrealizedPnl)} {investment.currency}
            </td>
            <td className="num" style={{ color: numberColor(investment.totalPnl) }}>
              {numberFormatter(investment.totalPnl)} {investment.currency}
            </td>
            <td className="num" style={{ color: numberColor(investment.irr) }}>
              {percentFormatter(investment.irr)}
            </td>
            <td className="num" style={{ color: numberColor(investment.mdm) }}>
              {percentFormatter(investment.mdm)}
            </td>
            <td className="num" style={{ color: numberColor(investment.twr) }}>
              {percentFormatter(investment.twr)}
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

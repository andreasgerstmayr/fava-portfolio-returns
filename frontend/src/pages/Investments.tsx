import { Alert } from "@mui/material";
import { Link } from "react-router";
import { createEnumParam, StringParam, useQueryParams, withDefault } from "use-query-params";
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

  const investments = data.investments.toSorted((a, b) => {
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
  const percentFormatter = fixedPercentFormatter;
  return (
    <table>
      <thead>
        <tr>
          <th
            data-sort=""
            data-order={sort.sortColumn === "name" ? sort.sortOrder : ""}
            onClick={() => handleSortChange("name")}
          >
            Name
          </th>
          <th>Units</th>
          <th
            data-sort=""
            data-order={sort.sortColumn === "cashIn" ? sort.sortOrder : ""}
            onClick={() => handleSortChange("cashIn")}
          >
            Cash In
          </th>
          <th
            data-sort=""
            data-order={sort.sortColumn === "cashOut" ? sort.sortOrder : ""}
            onClick={() => handleSortChange("cashOut")}
          >
            Cash Out
          </th>
          <th
            data-sort=""
            data-order={sort.sortColumn === "marketValue" ? sort.sortOrder : ""}
            onClick={() => handleSortChange("marketValue")}
          >
            Market Value
          </th>
          <th
            data-sort=""
            data-order={sort.sortColumn === "gains" ? sort.sortOrder : ""}
            onClick={() => handleSortChange("gains")}
          >
            Gains
          </th>
          <th
            data-sort=""
            data-order={sort.sortColumn === "irr" ? sort.sortOrder : ""}
            onClick={() => handleSortChange("irr")}
            title={ReturnsMethods.irr.label}
          >
            IRR
          </th>
          <th
            data-sort=""
            data-order={sort.sortColumn === "mdm" ? sort.sortOrder : ""}
            onClick={() => handleSortChange("mdm")}
            title={ReturnsMethods.mdm.label}
          >
            MDM
          </th>
          <th
            data-sort=""
            data-order={sort.sortColumn === "twr" ? sort.sortOrder : ""}
            onClick={() => handleSortChange("twr")}
            title={ReturnsMethods.twr.label}
          >
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
              {investment.cashIn != 0 && `${numberFormatter(investment.cashIn)} ${investment.currency}`}
            </td>
            <td className="num">
              {investment.cashOut != 0 && `${numberFormatter(investment.cashOut)} ${investment.currency}`}
            </td>
            <td className="num">
              {investment.marketValue != 0 && `${numberFormatter(investment.marketValue)} ${investment.currency}`}
            </td>
            <td
              className="num"
              style={{ color: investment.gains >= 0 ? POSITIVE_NUMBER_COLOR : NEGATIVE_NUMBER_COLOR }}
            >
              {numberFormatter(investment.gains)} {investment.currency}
            </td>
            <td className="num" style={{ color: investment.irr >= 0 ? POSITIVE_NUMBER_COLOR : NEGATIVE_NUMBER_COLOR }}>
              {percentFormatter(investment.irr)}
            </td>
            <td className="num" style={{ color: investment.mdm >= 0 ? POSITIVE_NUMBER_COLOR : NEGATIVE_NUMBER_COLOR }}>
              {percentFormatter(investment.mdm)}
            </td>
            <td className="num" style={{ color: investment.twr >= 0 ? POSITIVE_NUMBER_COLOR : NEGATIVE_NUMBER_COLOR }}>
              {percentFormatter(investment.twr)}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

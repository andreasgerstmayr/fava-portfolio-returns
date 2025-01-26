import { Alert } from "@mui/material";
import { Link } from "react-router";
import { useGroups } from "../api/groups";
import { Dashboard, DashboardRow, Panel } from "../components/Dashboard";
import { useToolbarContext } from "../components/Header/ToolbarProvider";
import { Loading } from "../components/Loading";
import { NEGATIVE_NUMBER_COLOR, POSITIVE_NUMBER_COLOR } from "../components/style";

export function Groups() {
  return (
    <Dashboard>
      <DashboardRow>
        <Panel title="Groups" help="Lists the groups defined in the beangrow configuration file.">
          <GroupsTable />
        </Panel>
      </DashboardRow>
    </Dashboard>
  );
}

export function GroupsTable() {
  const { targetCurrency } = useToolbarContext();
  const { isPending, error, data } = useGroups({ currency: targetCurrency });

  if (isPending) {
    return <Loading />;
  }
  if (error) {
    return <Alert severity="error">{error.message}</Alert>;
  }

  const numberFormatter = new Intl.NumberFormat(undefined, {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format;
  const percentFormatter = new Intl.NumberFormat(undefined, {
    style: "percent",
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format;

  return (
    <table>
      <thead>
        <tr>
          <th data-sort="string">Name</th>
          <th data-sort="string">Units</th>
          <th data-sort="num">Cash In</th>
          <th data-sort="num">Cash Out</th>
          <th data-sort="num">Market Value</th>
          <th data-sort="num">Returns</th>
          <th data-sort="num">Yield</th>
          <th data-sort="num">IRR</th>
          <th data-sort="num">TWR</th>
        </tr>
      </thead>
      <tbody>
        {data.groups.map((group, i) => (
          <tr key={i}>
            <td>
              <Link
                to={`/portfolio?${new URLSearchParams({ investments: "g:" + group.name, currency: group.currency })}`}
              >
                {group.name}
              </Link>
            </td>
            <td className="num">
              {group.units.map((unit, i) => (
                <span key={i}>
                  {numberFormatter(unit.number)} {unit.currency}
                  <br />
                </span>
              ))}
            </td>
            <td className="num">{group.cashIn != 0 && `${numberFormatter(group.cashIn)} ${group.currency}`}</td>
            <td className="num">{group.cashOut != 0 && `${numberFormatter(group.cashOut)} ${group.currency}`}</td>
            <td className="num">
              {group.marketValue != 0 && `${numberFormatter(group.marketValue)} ${group.currency}`}
            </td>
            <td
              className="num"
              style={{ color: group.returns >= 0 ? POSITIVE_NUMBER_COLOR : NEGATIVE_NUMBER_COLOR }}
              data-sort-value={group.returns}
            >
              {numberFormatter(group.returns)} {group.currency}
            </td>
            <td
              className="num"
              style={{ color: group.returnsPct >= 0 ? POSITIVE_NUMBER_COLOR : NEGATIVE_NUMBER_COLOR }}
              data-sort-value={group.returns}
            >
              {percentFormatter(group.returnsPct)}
            </td>
            <td
              className="num"
              style={{ color: group.irr >= 0 ? POSITIVE_NUMBER_COLOR : NEGATIVE_NUMBER_COLOR }}
              data-sort-value={group.returns}
            >
              {percentFormatter(group.irr)}
            </td>
            <td
              className="num"
              style={{ color: group.twr >= 0 ? POSITIVE_NUMBER_COLOR : NEGATIVE_NUMBER_COLOR }}
              data-sort-value={group.returns}
            >
              {percentFormatter(group.twr)}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

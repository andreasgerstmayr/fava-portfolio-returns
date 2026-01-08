import { Alert } from "@mui/material";
import { MouseEvent } from "react";
import { useMissingPrices } from "../api/missing_prices";
import { Dashboard, DashboardRow, Panel } from "../components/Dashboard";
import { Loading } from "../components/Loading";

export function MissingPrices() {
  const { isPending, error, data } = useMissingPrices();

  if (isPending) {
    return <Loading />;
  }
  if (error) {
    return <Alert severity="error">{error.message}</Alert>;
  }

  if (data.missingPrices.length === 0) {
    return <Alert severity="info">All required prices are available in the ledger.</Alert>;
  }

  const handleCommandsDblClick = (e: MouseEvent<HTMLPreElement>) => {
    const elem = e.currentTarget;
    const range = new Range();
    range.setStart(elem, 0);
    range.setEnd(elem, 1);
    window.getSelection()?.removeAllRanges();
    window.getSelection()?.addRange(range);
  };

  return (
    <Dashboard>
      <DashboardRow>
        <Panel title="Fetch Required Prices" help="Run the following commands and append the output to your ledger:">
          <pre onDoubleClick={handleCommandsDblClick}>{data.commands.join("\n")}</pre>
        </Panel>
      </DashboardRow>
      <DashboardRow>
        <Panel title="Missing Prices" help="This table shows dates where no accurate price directive was found.">
          <table>
            <thead>
              <tr>
                <th>Currency</th>
                <th>Required date</th>
                <th>Closest date in ledger</th>
                <th>Days late</th>
              </tr>
            </thead>
            <tbody>
              {data.missingPrices.map((price, i) => (
                <tr key={i}>
                  <td> {price.currency} </td>
                  <td>{price.requiredDate}</td>
                  <td>{price.actualDate}</td>
                  <td>{price.daysLate}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Panel>
      </DashboardRow>
    </Dashboard>
  );
}

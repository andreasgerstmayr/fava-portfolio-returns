import { Alert, alpha, FormControlLabel, FormGroup, Switch, useTheme } from "@mui/material";
import { DataGrid, GridColDef } from "@mui/x-data-grid";
import { createRoute, Link, stripSearchParams } from "@tanstack/react-router";
import { useTranslation } from "react-i18next";
import { z } from "zod";
import { Investment, useInvestments } from "../api/investments";
import { Dashboard, DashboardRow, Panel } from "../components/Dashboard";
import { useNumberFormatter, usePercentFormatter } from "../components/format";
import { useToolbarContext } from "../components/Header/ToolbarProvider";
import { Loading } from "../components/Loading";
import { useReturnsMethods } from "../components/ReturnsMethodSelection";
import { useSearchParam } from "../components/useSearchParam";
import { RootRoute } from "./__root";

const searchSchema = z.object({
  liquidated: z.boolean().default(false).catch(false),
});

export const InvestmentsRoute = createRoute({
  getParentRoute: () => RootRoute,
  path: "investments",
  validateSearch: searchSchema,
  search: {
    middlewares: [stripSearchParams({ liquidated: false })],
  },
  staticData: {
    showInvestmentsSelection: false,
  },
  component: Investments,
});

function Investments() {
  const { t } = useTranslation();
  const [includeLiquidated, setIncludeLiquidated] = useSearchParam(InvestmentsRoute, "liquidated");

  return (
    <Dashboard>
      <DashboardRow>
        <Panel title={t("Investments")} help={t("Lists the investments defined in the beangrow configuration file.")}>
          <InvestmentsTable
            groupBy="currency"
            includeLiquidated={includeLiquidated}
            setIncludeLiquidated={setIncludeLiquidated}
          />
        </Panel>
      </DashboardRow>
    </Dashboard>
  );
}

interface InvestmentsTableProps {
  groupBy: "group" | "currency";
  includeLiquidated: boolean;
  setIncludeLiquidated: (x: boolean) => void;
}

export function InvestmentsTable({ groupBy, includeLiquidated, setIncludeLiquidated }: InvestmentsTableProps) {
  const { t } = useTranslation();
  const theme = useTheme();
  const { targetCurrency } = useToolbarContext();
  const numberFormatter = useNumberFormatter();
  const fixedPercentFormatter = usePercentFormatter({ fixed: true });
  const { isPending, error, data } = useInvestments({ targetCurrency, groupBy });
  const returnsMethods = useReturnsMethods();

  if (isPending) {
    return <Loading />;
  }
  if (error) {
    return <Alert severity="error">{error.message}</Alert>;
  }

  if (Object.keys(data.investments).length === 0) {
    return (
      <Alert severity="info">
        {groupBy === "group"
          ? t("No groups defined in the beangrow configuration.")
          : t("No investments defined in the beangrow configuration.")}
      </Alert>
    );
  }

  let investments = data.investments;
  if (!includeLiquidated) {
    investments = investments.filter((i) => i.marketValue > 0);
  }

  // cost value, market value and unrealized P/L will be zero once the investment is liquidated
  // realized P/L is zero if investment was never sold
  const nonZero = (x: number) => Math.abs(x) >= 0.01;

  const columns: GridColDef<Investment>[] = [
    {
      field: "name",
      headerName: t("Name"),
      flex: 1, // expand to remaining space
      renderCell: ({ row }) => (
        <Link to="/portfolio" search={{ investments: row.id, currency: row.currency }}>
          {row.name}
        </Link>
      ),
    },
    {
      field: "units",
      headerName: t("Units"),
      headerAlign: "center",
      align: "right",
      minWidth: 130,
      renderCell: ({ row }) => (
        <div>
          {row.units.map((unit, i) => (
            <span key={i}>
              {numberFormatter(unit.number)} {unit.currency}
              <br />
            </span>
          ))}
        </div>
      ),
    },
    {
      field: "costValue",
      headerName: t("Cost Value"),
      headerAlign: "center",
      align: "right",
      minWidth: 130,
      valueFormatter: (_value, row) =>
        nonZero(row.costValue) ? `${numberFormatter(row.costValue)} ${row.currency}` : "",
    },
    {
      field: "marketValue",
      headerName: t("Market Value"),
      headerAlign: "center",
      align: "right",
      minWidth: 130,
      valueFormatter: (_value, row) =>
        nonZero(row.marketValue) ? `${numberFormatter(row.marketValue)} ${row.currency}` : "",
    },
    {
      field: "realizedPnl",
      headerName: t("Realized P/L"),
      description: t("Realized Profit and Loss: P&L from sold assets"),
      headerAlign: "center",
      align: "right",
      minWidth: 130,
      valueFormatter: (_value, row) =>
        nonZero(row.realizedPnl) ? `${numberFormatter(row.realizedPnl)} ${row.currency}` : "",
      cellClassName: ({ row }) => (row.realizedPnl >= 0 ? "positive" : "negative"),
    },
    {
      field: "unrealizedPnl",
      headerName: t("Unrealized P/L"),
      description: t("Unrealized Profit and Loss: P&L from open positions (excluding fees)"),
      headerAlign: "center",
      align: "right",
      minWidth: 130,
      valueFormatter: (_value, row) =>
        nonZero(row.unrealizedPnl) ? `${numberFormatter(row.unrealizedPnl)} ${row.currency}` : "",
      cellClassName: ({ row }) => (row.unrealizedPnl >= 0 ? "positive" : "negative"),
    },
    {
      field: "totalPnl",
      headerName: t("Total P/L"),
      description: t("Total Profit and Loss"),
      headerAlign: "center",
      align: "right",
      minWidth: 130,
      valueFormatter: (_value, row) => `${numberFormatter(row.totalPnl)} ${row.currency}`,
      cellClassName: ({ row }) => (row.totalPnl >= 0 ? "positive" : "negative"),
    },
    {
      field: "irr",
      headerName: t("IRR"),
      description: returnsMethods.irr.label,
      headerAlign: "center",
      align: "right",
      minWidth: 80,
      valueFormatter: (_value, row) => fixedPercentFormatter(row.irr),
      cellClassName: ({ row }) => (row.irr >= 0 ? "positive" : "negative"),
    },
    {
      field: "mdm",
      headerName: t("MDM"),
      description: returnsMethods.mdm.label,
      headerAlign: "center",
      align: "right",
      minWidth: 80,
      valueFormatter: (_value, row) => fixedPercentFormatter(row.mdm),
      cellClassName: ({ row }) => (row.mdm >= 0 ? "positive" : "negative"),
    },
    {
      field: "twr",
      headerName: t("TWR"),
      description: returnsMethods.twr.label,
      headerAlign: "center",
      align: "right",
      minWidth: 80,
      valueFormatter: (_value, row) => fixedPercentFormatter(row.twr),
      cellClassName: ({ row }) => (row.twr >= 0 ? "positive" : "negative"),
    },
  ];

  return (
    <>
      <DataGrid
        columns={columns}
        rows={investments}
        density="compact"
        getRowHeight={() => "auto"}
        getRowClassName={(params) => (params.indexRelativeToCurrentPage % 2 === 0 ? "even" : "odd")}
        initialState={{
          sorting: {
            sortModel: [{ field: "name", sort: "asc" }],
          },
        }}
        sx={{
          ".MuiDataGrid-cell": {
            display: "flex",
            alignItems: "center",
            px: 1,
            py: 0.5,
          },
          ".MuiDataGrid-cell:not([data-field='name'])": {
            fontFamily: '"Fira Mono", monospace',
          },
          ".even": {
            backgroundColor: theme.palette.action.hover,
          },
          ".MuiDataGrid-row:hover": {
            backgroundColor: alpha(theme.palette.action.hover, 0.1),
          },
          ".positive": {
            color: theme.pnl.profit,
          },
          ".negative": {
            color: theme.pnl.loss,
          },
        }}
      />
      <FormGroup>
        <FormControlLabel
          control={<Switch checked={includeLiquidated} onChange={(_, value) => setIncludeLiquidated(value)} />}
          label={t("Include liquidated investments")}
        />
      </FormGroup>
    </>
  );
}

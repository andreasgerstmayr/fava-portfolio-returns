import { Alert, FormControlLabel, FormGroup, Stack, Switch, Theme, useTheme } from "@mui/material";
import { DataGrid, GridColDef } from "@mui/x-data-grid";
import { createRoute } from "@tanstack/react-router";
import { Fragment, ReactNode, useState } from "react";
import { useTranslation } from "react-i18next";
import {
  AssetAllocationAsset,
  AssetAllocationClassReport,
  AssetAllocationClassRow,
  AssetAllocationCommodityReport,
  AssetAllocationPortfolio,
  useAssetAllocation,
} from "../api/asset_allocation";
import { Dashboard, DashboardRow, Panel } from "../components/Dashboard";
import { EChart, EChartsSpec } from "../components/EChart";
import { useCurrencyFormatter, usePercentFormatter } from "../components/format";
import { useToolbarContext } from "../components/Header/ToolbarProvider";
import { Loading } from "../components/Loading";
import { PortfolioSelection } from "../components/PortfolioSelection";
import { RootRoute } from "./__root";

export const AssetAllocationRoute = createRoute({
  getParentRoute: () => RootRoute,
  path: "asset_allocation",
  staticData: {
    showInvestmentsSelection: false,
  },
  component: AssetAllocation,
});

const EXAMPLE_DIRECTIVE = `2010-01-01 custom "fava-extension" "fava_portfolio_returns" "{
  'beangrow_config': 'beangrow.pbtxt',
  'asset_allocation_config': 'asset-allocation.yaml',
}"`;

const EXAMPLE_YAML = `portfolios:
  - name: My Portfolio
    accounts:
      - "^Assets:Broker:Investments:"
    allocation:               # the target asset allocation, by...
      commodities:            # ... commodity, should sum to 100%
        - commodity: ETF_FOO
          target: 60%
        - commodity: ETF_BAR
          target: 40%
      classes:                # ... asset class, should sum to 100%
        - asset-class: stocks
          target: 70%
        - asset-class: bonds
          target: 30%`;

const MONO = '"Fira Mono", monospace';

/** shared DataGrid styling so the commodity and asset-class tables render identically */
function gridBaseSx(theme: Theme) {
  return {
    ".MuiDataGrid-cell:not([data-field='commodity']):not([data-field='assetClass'])": {
      fontFamily: MONO,
    },
    ".diverged": {
      color: theme.pnl.loss,
      fontWeight: "bold",
    },
  };
}

const commodityLabel = (commodity: string, name: string) => (name !== commodity ? `${commodity} (${name})` : commodity);

/** returns a formatter turning a signed deviation value into a Buy/Sell suggestion */
function useRebalanceFormatter(currency: string) {
  const { t } = useTranslation();
  const currencyFormatter = useCurrencyFormatter(currency);
  return (value: number) => {
    if (Math.abs(value) < 0.01) {
      return "—";
    }
    // positive deviation => overweight => sell; negative => underweight => buy
    return value > 0
      ? t("Sell {{amount}}", { amount: currencyFormatter(Math.abs(value)) })
      : t("Buy {{amount}}", { amount: currencyFormatter(Math.abs(value)) });
  };
}

function AssetAllocation() {
  const { t } = useTranslation();
  const { targetCurrency } = useToolbarContext();
  const [minimize, setMinimize] = useState(false);
  // empty means "show all" (the default); adding names restricts the view to them
  const [selectedPortfolios, setSelectedPortfolios] = useState<string[]>([]);
  const { isPending, error, data } = useAssetAllocation({ targetCurrency, minimize });

  if (isPending) {
    return <Loading />;
  }
  if (error) {
    return <Alert severity="error">{error.message}</Alert>;
  }

  if (data.portfolios.length === 0) {
    return (
      <Dashboard>
        <DashboardRow>
          <Panel
            title={t("Asset Allocation")}
            help={t(
              "Compares the current asset allocation of your portfolios against a target allocation. Point the 'asset_allocation_config' option to a YAML file:",
            )}
          >
            <pre>{EXAMPLE_DIRECTIVE}</pre>
            <p>{t("Example asset-allocation.yaml:")}</p>
            <pre>{EXAMPLE_YAML}</pre>
            <p>
              {t("Asset classes are read from each commodity's 'asset-class' metadata (hierarchical, ':'-separated).")}
            </p>
          </Panel>
        </DashboardRow>
      </Dashboard>
    );
  }

  const hasClassReport = data.portfolios.some((portfolio) => portfolio.classReport !== null);
  const allNames = data.portfolios.map((portfolio) => portfolio.name);
  const visiblePortfolios =
    selectedPortfolios.length === 0
      ? data.portfolios
      : data.portfolios.filter((portfolio) => selectedPortfolios.includes(portfolio.name));

  return (
    <Dashboard>
      {data.portfolios.length > 1 && (
        <DashboardRow sx={{ alignItems: "center", flexWrap: "wrap" }}>
          <PortfolioSelection
            label={t("Portfolios")}
            options={allNames}
            selected={selectedPortfolios}
            setSelected={setSelectedPortfolios}
          />
        </DashboardRow>
      )}
      {/* each allocation of a portfolio (by commodity, by class) is its own report */}
      {visiblePortfolios.map((portfolio) => (
        <Fragment key={portfolio.name}>
          {portfolio.commodityReport && (
            <DashboardRow>
              <ReportPanel
                portfolio={portfolio}
                title={t("{{portfolio}} (by commodity)", { portfolio: portfolio.name })}
              >
                <CommoditySection portfolio={portfolio} report={portfolio.commodityReport} />
              </ReportPanel>
            </DashboardRow>
          )}
          {portfolio.classReport && (
            <DashboardRow>
              <ReportPanel portfolio={portfolio} title={t("{{portfolio}} (by class)", { portfolio: portfolio.name })}>
                <ClassSection portfolio={portfolio} report={portfolio.classReport} />
              </ReportPanel>
            </DashboardRow>
          )}
        </Fragment>
      ))}
      {hasClassReport && (
        <DashboardRow>
          <FormGroup>
            <FormControlLabel
              control={<Switch checked={minimize} onChange={(e) => setMinimize(e.target.checked)} />}
              label={t("Minimize the number of trades when rebalancing asset classes")}
            />
          </FormGroup>
        </DashboardRow>
      )}
    </Dashboard>
  );
}

/** one top-level report: a single allocation of a single portfolio */
function ReportPanel({
  portfolio,
  title,
  children,
}: {
  portfolio: AssetAllocationPortfolio;
  title: string;
  children: ReactNode;
}) {
  const { t } = useTranslation();
  const currencyFormatter = useCurrencyFormatter(portfolio.currency);
  const [collapsed, setCollapsed] = useState(false);

  // The band is per portfolio (a portfolio may tighten the file-level one, an
  // individual commodity/class the portfolio's), and states a *rule*, not a
  // number: what it works out to depends on each row's own target, hence the
  // Threshold column below.
  const accounts = portfolio.accounts.join(", ");
  const total = currencyFormatter(portfolio.totalValue);
  const help = t(
    "Accounts: {{accounts}} — Total value: {{total}} — Divergence threshold: ±min({{ofPortfolio}}% of the portfolio, {{ofTarget}}% of the target), see the Threshold column",
    { accounts, total, ofPortfolio: portfolio.band.ofPortfolio, ofTarget: portfolio.band.ofTarget },
  );

  return (
    <Panel
      title={title}
      help={help}
      sx={{ flex: 1 }}
      collapsible
      collapsed={collapsed}
      onToggleCollapsed={() => setCollapsed((c) => !c)}
    >
      <Stack sx={{ gap: 2 }}>
        {/* the portfolio's holdings, hence repeated in each of its reports */}
        {portfolio.unpriced.map((commodity) => (
          <Alert severity="warning" key={commodity}>
            {t("Held commodity {{commodity}} has no known price and is excluded from the valuation.", {
              commodity: commodity,
            })}
          </Alert>
        ))}
        {children}
      </Stack>
    </Panel>
  );
}

/** shared divergence + target-sum alerts for a sub-report */
function ReportAlerts({
  diverged,
  targetSum,
  targetSumOk,
}: {
  diverged: boolean;
  targetSum: number;
  targetSumOk: boolean;
}) {
  const { t } = useTranslation();
  return (
    <>
      {diverged && (
        <Alert severity="warning">
          {t("Some assets diverge from the target allocation beyond their own divergence threshold.")}
        </Alert>
      )}
      {!targetSumOk && (
        <Alert severity="error">
          {t("The target allocation sums to {{sum}}%, expected 100%.", { sum: targetSum })}
        </Alert>
      )}
    </>
  );
}

function AllocationChart({
  labels,
  names,
  target,
  current,
  over,
  thresholds,
  height,
}: {
  labels: string[];
  /** full name of each label (e.g. the fund name), shown in the tooltip */
  names?: string[];
  target: number[];
  current: number[];
  /** whether each label diverges beyond its own threshold (drawn bold + red) */
  over: boolean[];
  /** each label's divergence threshold in percentage points (tooltip wording) */
  thresholds: number[];
  height: string;
}) {
  const { t } = useTranslation();
  const theme = useTheme();
  const percentFormatter = usePercentFormatter();
  // reverse so the first item appears at the top of the (inverted) category axis
  const idx = labels.map((_, i) => i).reverse();
  const axisLabels = idx.map((i) => labels[i]);
  const pct = (value: number) => percentFormatter(value / 100);
  // labels of over-threshold rows, highlighted on the category axis
  const overLabels = new Set(labels.filter((_, i) => over[i]));
  // hovering an axis label pops up that row's tooltip, which spells out the full name
  const axisLabelTooltip = names !== undefined;

  const option: EChartsSpec = {
    tooltip: {
      trigger: "axis",
      axisPointer: { type: "shadow" },
      // one bar (Current) plus a Target marker per row; show both values cleanly
      formatter: (params) => {
        const items = Array.isArray(params) ? params : [params];
        const category = items[0]?.name ?? "";
        const name = names?.[labels.indexOf(category)];
        const seriesValue = (name: string) => {
          const raw = items.find((item) => item.seriesName === name)?.value;
          return Array.isArray(raw) ? Number(raw[0]) : Number(raw);
        };
        const lines = items.map((item) => {
          const raw = item.value;
          const value = Array.isArray(raw) ? Number(raw[0]) : Number(raw);
          return `${item.marker ?? ""} ${item.seriesName ?? ""}: ${pct(value)}`;
        });
        // for a highlighted (over-threshold) row, explain the divergence and its size
        if (overLabels.has(category)) {
          const dev = seriesValue(t("Current")) - seriesValue(t("Target"));
          lines.push(
            t("⚠ Diverges by {{dev}} from target (beyond ±{{threshold}})", {
              dev: `${dev >= 0 ? "+" : ""}${pct(dev)}`,
              // derived from this row's own target, so rarely a round number
              threshold: pct(thresholds[labels.indexOf(category)]),
            }),
          );
        }
        return [name ? commodityLabel(category, name) : category, ...lines].join("<br/>");
      },
    },
    legend: { bottom: 0 },
    // extra bottom margin so the x-axis labels clear the legend below them
    grid: { left: 120, right: 20, top: 10, bottom: 55 },
    xAxis: {
      type: "value",
      axisLabel: { formatter: (value: number) => pct(value) },
    },
    yAxis: {
      type: "category",
      data: axisLabels,
      triggerEvent: axisLabelTooltip,
      axisLabel: {
        formatter: (label: string) => (overLabels.has(label) ? `{over|${label}}` : label),
        rich: { over: { color: theme.pnl.loss, fontWeight: "bold" } },
      },
    },
    series: [
      {
        type: "bar",
        name: t("Current"),
        barWidth: "55%",
        data: idx.map((i) => current[i]),
      },
      {
        // target drawn as a thin vertical marker across the bar (bullet-chart style),
        // like Fava's budget bars: the bar shows the current value, the tick the target
        type: "scatter",
        name: t("Target"),
        symbol: "rect",
        symbolSize: [3, 22],
        itemStyle: { color: theme.palette.text.primary },
        z: 3,
        data: labels.map((label, i) => [target[i], label]),
      },
    ],
    // the axis labels are outside the grid, so the axis tooltip does not cover them:
    // show/hide it by hand while the pointer is over one
    onMouseOver: axisLabelTooltip
      ? (params, chart) => {
          if (params.componentType !== "yAxis") {
            return;
          }
          const dataIndex = axisLabels.indexOf(String(params.value));
          if (dataIndex >= 0) {
            // pin it to the pointer: by default it lands on the bar, which sits at a
            // different distance from each label
            const { offsetX = 0, offsetY = 0 } = params.event ?? {};
            chart.dispatchAction({ type: "showTip", seriesIndex: 0, dataIndex, position: [offsetX + 12, offsetY] });
          }
        }
      : undefined,
    onMouseOut: axisLabelTooltip
      ? (params, chart) => {
          if (params.componentType === "yAxis") {
            chart.dispatchAction({ type: "hideTip" });
          }
        }
      : undefined,
  };

  return <EChart height={height} option={option} />;
}

function CommoditySection({
  portfolio,
  report,
}: {
  portfolio: AssetAllocationPortfolio;
  report: AssetAllocationCommodityReport;
}) {
  const { t } = useTranslation();
  const currencyFormatter = useCurrencyFormatter(portfolio.currency);
  const height = `${Math.max(140, report.assets.length * 34 + 80)}px`;

  return (
    <Stack sx={{ gap: 1 }}>
      <ReportAlerts {...report} />
      {report.unconfigured.map((holding) => (
        <Alert severity="warning" key={holding.commodity}>
          {t("Held commodity {{commodity}} ({{value}}) is not part of the target allocation.", {
            commodity: holding.commodity,
            value: currencyFormatter(holding.value),
          })}
        </Alert>
      ))}
      <AllocationChart
        labels={report.assets.map((a) => a.commodity)}
        names={report.assets.map((a) => a.name)}
        target={report.assets.map((a) => a.targetPct)}
        current={report.assets.map((a) => a.currentPct)}
        over={report.assets.map((a) => a.over)}
        thresholds={report.assets.map((a) => a.thresholdPct)}
        height={height}
      />
      <CommodityTable portfolio={portfolio} report={report} />
    </Stack>
  );
}

function CommodityTable({
  portfolio,
  report,
}: {
  portfolio: AssetAllocationPortfolio;
  report: AssetAllocationCommodityReport;
}) {
  const { t } = useTranslation();
  const theme = useTheme();
  const currencyFormatter = useCurrencyFormatter(portfolio.currency);
  const percentFormatter = usePercentFormatter({ fixed: true });
  const rebalance = useRebalanceFormatter(portfolio.currency);

  const columns: GridColDef<AssetAllocationAsset>[] = [
    {
      field: "commodity",
      headerName: t("Commodity"),
      flex: 1,
      renderCell: ({ row }) => commodityLabel(row.commodity, row.name),
    },
    {
      field: "targetPct",
      headerName: t("Target"),
      headerAlign: "center",
      align: "right",
      minWidth: 90,
      valueFormatter: (value: number) => percentFormatter(value / 100),
    },
    {
      field: "currentPct",
      headerName: t("Current"),
      headerAlign: "center",
      align: "right",
      minWidth: 90,
      valueFormatter: (value: number) => percentFormatter(value / 100),
    },
    {
      field: "value",
      headerName: t("Value"),
      headerAlign: "center",
      align: "right",
      minWidth: 120,
      valueFormatter: (value: number) => currencyFormatter(value),
    },
    {
      field: "devPct",
      headerName: t("Deviation"),
      description: t("Deviation from the target allocation in percentage points"),
      headerAlign: "center",
      align: "right",
      minWidth: 100,
      valueFormatter: (value: number) => `${value >= 0 ? "+" : ""}${percentFormatter(value / 100)}`,
      cellClassName: ({ row }) => (row.over ? "diverged" : ""),
    },
    {
      // always shown: every band is derived from its own target, so this is the
      // only place the one that applies to a row can be read
      field: "thresholdPct",
      headerName: t("Threshold"),
      description: t("Divergence threshold beyond which this row is flagged, derived from its target"),
      headerAlign: "center",
      align: "right",
      minWidth: 100,
      valueFormatter: (value: number) => `±${percentFormatter(value / 100)}`,
    },
    {
      field: "devValue",
      headerName: t("Rebalance"),
      headerAlign: "center",
      align: "right",
      minWidth: 140,
      valueFormatter: (value: number) => rebalance(value),
    },
  ];

  return (
    <DataGrid
      columns={columns}
      rows={report.assets}
      getRowId={(row) => row.commodity}
      density="compact"
      hideFooter
      disableColumnMenu
      initialState={{
        sorting: {
          sortModel: [{ field: "value", sort: "desc" }],
        },
      }}
      sx={gridBaseSx(theme)}
    />
  );
}

function ClassSection({
  portfolio,
  report,
}: {
  portfolio: AssetAllocationPortfolio;
  report: AssetAllocationClassReport;
}) {
  const { t } = useTranslation();
  const currencyFormatter = useCurrencyFormatter(portfolio.currency);
  const height = `${Math.max(140, report.classes.length * 34 + 80)}px`;

  return (
    <Stack sx={{ gap: 1 }}>
      <ReportAlerts {...report} />
      {report.unconfigured.map((holding) => (
        <Alert severity="warning" key={holding.commodity}>
          {t("Held commodity {{commodity}} ({{value}}) is excluded from the class allocation: {{reason}}.", {
            commodity: holding.commodity,
            value: currencyFormatter(holding.value),
            reason: holding.reason ?? "",
          })}
        </Alert>
      ))}
      <AllocationChart
        labels={report.classes.map((c) => c.assetClass)}
        target={report.classes.map((c) => c.targetPct)}
        current={report.classes.map((c) => c.currentPct)}
        over={report.classes.map((c) => c.over)}
        thresholds={report.classes.map((c) => c.thresholdPct)}
        height={height}
      />
      <ClassTable portfolio={portfolio} report={report} />
    </Stack>
  );
}

function ClassTable({
  portfolio,
  report,
}: {
  portfolio: AssetAllocationPortfolio;
  report: AssetAllocationClassReport;
}) {
  const { t } = useTranslation();
  const theme = useTheme();
  const currencyFormatter = useCurrencyFormatter(portfolio.currency);
  const percentFormatter = usePercentFormatter({ fixed: true });
  const rebalance = useRebalanceFormatter(portfolio.currency);

  // Each row is one asset class; its per-commodity rebalance breakdown is
  // rendered as aligned sub-lines inside the same row. This keeps the table
  // sortable (like the commodity table) while ensuring a column sort always
  // orders by the class-level value, never by an individual commodity.
  const subLine = { opacity: 0.7 };

  const notes = (row: AssetAllocationClassRow) => {
    const lines: string[] = [];
    if (row.noHoldings && row.devValue !== 0) {
      lines.push(t("(no current holdings in this class)"));
    }
    if (row.shortfall > 0) {
      lines.push(
        t("(short {{amount}} — cannot reconcile within the commodity ±threshold)", {
          amount: currencyFormatter(row.shortfall),
        }),
      );
    }
    return lines;
  };

  const columns: GridColDef<AssetAllocationClassRow>[] = [
    {
      field: "assetClass",
      headerName: t("Asset class / Commodity"),
      flex: 1,
      renderCell: ({ row }) => (
        <Stack sx={{ gap: 0.25, py: 0.5 }}>
          <span style={{ fontWeight: "bold" }}>{row.assetClass}</span>
          {row.members.map((member) => (
            <span key={member.commodity} style={{ paddingLeft: 16, ...subLine }}>
              {commodityLabel(member.commodity, member.name)}
            </span>
          ))}
          {notes(row).map((note) => (
            <span key={note} style={{ paddingLeft: 16, fontStyle: "italic", ...subLine }}>
              {note}
            </span>
          ))}
        </Stack>
      ),
    },
    {
      field: "targetPct",
      headerName: t("Target"),
      headerAlign: "center",
      align: "right",
      minWidth: 90,
      valueFormatter: (value: number) => percentFormatter(value / 100),
    },
    {
      field: "currentPct",
      headerName: t("Current"),
      headerAlign: "center",
      align: "right",
      minWidth: 90,
      valueFormatter: (value: number) => percentFormatter(value / 100),
    },
    {
      field: "value",
      headerName: t("Value"),
      headerAlign: "center",
      align: "right",
      minWidth: 120,
      renderCell: ({ row }) => (
        <Stack sx={{ gap: 0.25, py: 0.5, width: "100%", alignItems: "flex-end" }}>
          <span>{currencyFormatter(row.value)}</span>
          {row.members.map((member) => (
            <span key={member.commodity} style={subLine}>
              {currencyFormatter(member.value)}
            </span>
          ))}
        </Stack>
      ),
    },
    {
      field: "devPct",
      headerName: t("Deviation"),
      description: t("Deviation from the target allocation in percentage points"),
      headerAlign: "center",
      align: "right",
      minWidth: 100,
      valueFormatter: (value: number) => `${value >= 0 ? "+" : ""}${percentFormatter(value / 100)}`,
      cellClassName: ({ row }) => (row.over ? "diverged" : ""),
    },
    {
      // always shown: every band is derived from its own target, so this is the
      // only place the one that applies to a row can be read
      field: "thresholdPct",
      headerName: t("Threshold"),
      description: t("Divergence threshold beyond which this row is flagged, derived from its target"),
      headerAlign: "center",
      align: "right",
      minWidth: 100,
      valueFormatter: (value: number) => `±${percentFormatter(value / 100)}`,
    },
    {
      field: "devValue",
      headerName: t("Rebalance"),
      headerAlign: "center",
      align: "right",
      minWidth: 140,
      renderCell: ({ row }) => (
        <Stack sx={{ gap: 0.25, py: 0.5, width: "100%", alignItems: "flex-end" }}>
          <span>{rebalance(row.devValue)}</span>
          {row.members.map((member) => (
            <span key={member.commodity} style={subLine}>
              {rebalance(member.tradeValue)}
            </span>
          ))}
        </Stack>
      ),
    },
  ];

  return (
    <DataGrid
      columns={columns}
      rows={report.classes}
      getRowId={(row) => row.assetClass}
      density="compact"
      getRowHeight={() => "auto"}
      hideFooter
      disableColumnMenu
      initialState={{
        sorting: {
          sortModel: [{ field: "value", sort: "desc" }],
        },
      }}
      sx={{
        ...gridBaseSx(theme),
        ".MuiDataGrid-cell": {
          display: "flex",
          alignItems: "flex-start",
        },
      }}
    />
  );
}

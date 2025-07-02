import { Card, MenuItem, Select, Stack, SxProps, Theme, useTheme } from "@mui/material";
import React from "react";
import { NumberParam, useQueryParam, withDefault } from "use-query-params";

interface DashboardProps {
  children?: React.ReactNode;
}
export function Dashboard({ children }: DashboardProps) {
  const theme = useTheme();
  return (
    <Stack
      sx={{
        flexDirection: "column",
        // remove 1.5em padding from <article>
        mx: "-1.5em",
        marginBottom: "-1.5em",
        padding: "1.5em",
        gap: 2,
        backgroundColor: theme.palette.mode === "dark" ? undefined : "#FAFBFB",
      }}
    >
      {children}
    </Stack>
  );
}
interface DashboardRow {
  sx?: SxProps<Theme>;
  children?: React.ReactNode;
}

export function DashboardRow({ sx, children }: DashboardRow) {
  return <Stack sx={{ flexDirection: "row", gap: 2, alignItems: "flex-start", ...sx }}>{children}</Stack>;
}

interface PanelProps {
  title: string;
  help?: string;
  topRightElem?: React.ReactNode;
  sx?: SxProps<Theme>;
  children: React.ReactNode;
}

export function Panel({ title, help, topRightElem, sx, children }: PanelProps) {
  return (
    <Card variant="outlined" sx={{ flex: 1, padding: 2, overflow: "auto", ...sx }}>
      <Stack sx={{ flexDirection: "row", justifyContent: "space-between" }}>
        <h3>{title}</h3>
        {topRightElem}
      </Stack>
      {help && <p style={{ whiteSpace: "pre-line" }}>{help}</p>}
      {children}
    </Card>
  );
}

interface PanelGroupProps {
  param: string;
  labels: string[];
  children: React.ReactElement<PanelProps>[];
}

const ActivePanelParam = withDefault(NumberParam, 0);

export function PanelGroup({ param, labels, children }: PanelGroupProps) {
  const [activePanelIdx, setActivePanelIdx] = useQueryParam(param, ActivePanelParam);
  const activePanel = children[activePanelIdx];

  const select = (
    <Select
      value={activePanelIdx}
      onChange={(e) => setActivePanelIdx(e.target.value as number)}
      displayEmpty
      size="small"
    >
      {labels.map((label, i) => (
        <MenuItem key={i} value={i}>
          {label}
        </MenuItem>
      ))}
    </Select>
  );

  return <Panel {...activePanel.props} topRightElem={select}></Panel>;
}

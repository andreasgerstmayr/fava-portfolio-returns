import { Card, MenuItem, Select, Stack, SxProps, Theme, useTheme } from "@mui/material";
import React from "react";

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
      {help && <p style={{ whiteSpace: "pre-line", maxWidth: "80%" }}>{help}</p>}
      {children}
    </Card>
  );
}

interface Option<TKey> {
  key: TKey;
  label: string;
}

interface PanelGroupProps<TKey> {
  options: Option<TKey>[];
  selected: TKey;
  setSelected: (x: TKey) => void;
  children: React.ReactElement<PanelProps>[];
}

export function PanelGroup<TKey extends string>({ options, selected, setSelected, children }: PanelGroupProps<TKey>) {
  const activePanelIdx = options.findIndex((option) => option.key == selected);
  const activePanel = children[Math.max(activePanelIdx, 0)];

  const select = (
    <Select value={selected} onChange={(e) => setSelected(e.target.value as TKey)} displayEmpty size="small">
      {options.map((option) => (
        <MenuItem key={option.key} value={option.key}>
          {option.label}
        </MenuItem>
      ))}
    </Select>
  );

  return <Panel {...activePanel.props} topRightElem={select} />;
}

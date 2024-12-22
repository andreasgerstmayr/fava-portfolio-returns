import { Box, Stack } from "@mui/material";
import { useMatches } from "react-router";
import { DateRangeSelection } from "./DateRangeSelection";
import { GlobalInvestmentsSelection } from "./GlobalInvestmentsSelection";
import { TargetCurrencySelection } from "./TargetCurrencySelection";

export function Toolbar() {
  const matches = useMatches();
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const handle = matches.pop()?.handle as Record<string, any> | undefined;
  const showInvestmentsSelection = handle?.showInvestmentsSelection !== false;
  const showCurrencySelection = handle?.showCurrencySelection !== false;

  return (
    <Stack sx={{ flexDirection: "row", justifyContent: "flex-end", alignItems: "center", gap: 2, marginBottom: 2 }}>
      {showInvestmentsSelection && <GlobalInvestmentsSelection />}
      <DateRangeSelection />
      {showCurrencySelection && (
        <Box>
          <TargetCurrencySelection />
        </Box>
      )}
    </Stack>
  );
}

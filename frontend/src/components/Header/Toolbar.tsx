import { Box, Stack } from "@mui/material";
import { useMatches } from "@tanstack/react-router";
import { DateRangeSelection } from "./DateRangeSelection";
import { GlobalInvestmentsSelection } from "./GlobalInvestmentsSelection";
import { TargetCurrencySelection } from "./TargetCurrencySelection";

export function Toolbar() {
  const matches = useMatches();
  const staticData = matches[matches.length - 1]?.staticData;
  const showInvestmentsSelection = staticData?.showInvestmentsSelection !== false;
  const showDateRangeSelection = staticData?.showDateRangeSelection !== false;
  const showCurrencySelection = staticData?.showCurrencySelection !== false;

  return (
    <Stack sx={{ flexDirection: "row", justifyContent: "flex-end", alignItems: "center", gap: 2, marginBottom: 2 }}>
      {showInvestmentsSelection && <GlobalInvestmentsSelection />}
      {showDateRangeSelection && <DateRangeSelection />}
      {showCurrencySelection && (
        <Box>
          <TargetCurrencySelection />
        </Box>
      )}
    </Stack>
  );
}

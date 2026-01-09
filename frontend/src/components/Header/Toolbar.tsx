import { Box, Stack } from "@mui/material";
import { useMatches } from "react-router";
import { DateRangeSelection } from "./DateRangeSelection";
import { GlobalInvestmentsSelection } from "./GlobalInvestmentsSelection";
import { TargetCurrencySelection } from "./TargetCurrencySelection";

interface Handle {
  showInvestmentsSelection: boolean;
  showDateRangeSelection: boolean;
  showCurrencySelection: boolean;
}

export function Toolbar() {
  const matches = useMatches();
  const handle = matches[matches.length - 1]?.handle as Handle | undefined;
  const showInvestmentsSelection = handle?.showInvestmentsSelection !== false;
  const showDateRangeSelection = handle?.showDateRangeSelection !== false;
  const showCurrencySelection = handle?.showCurrencySelection !== false;

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

import { ToggleButton, ToggleButtonGroup } from "@mui/material";
import { useToolbarContext } from "./ToolbarProvider";

export function TargetCurrencySelection() {
  const { targetCurrency, setTargetCurrency, config: toolbarResponse } = useToolbarContext();

  return (
    <ToggleButtonGroup value={targetCurrency} onChange={(_e, value) => setTargetCurrency(value)} exclusive>
      {toolbarResponse.operatingCurrencies.map((currency) => (
        <ToggleButton key={currency} value={currency}>
          {currency}
        </ToggleButton>
      ))}
    </ToggleButtonGroup>
  );
}

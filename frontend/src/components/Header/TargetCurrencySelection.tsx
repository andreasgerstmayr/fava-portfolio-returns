import { ToggleButton, ToggleButtonGroup } from "@mui/material";
import { useToolbarContext } from "./ToolbarProvider";

export function TargetCurrencySelection() {
  const { targetCurrency, setTargetCurrency, config } = useToolbarContext();

  return (
    <ToggleButtonGroup value={targetCurrency} onChange={(_e, value) => setTargetCurrency(value)} exclusive>
      {config.operatingCurrencies.map((currency) => (
        <ToggleButton key={currency} value={currency}>
          {currency}
        </ToggleButton>
      ))}
    </ToggleButtonGroup>
  );
}

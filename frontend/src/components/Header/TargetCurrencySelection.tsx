import { ToggleButton, ToggleButtonGroup } from "@mui/material";
import { SyntheticEvent } from "react";
import { useToolbarContext } from "./ToolbarProvider";

export function TargetCurrencySelection() {
  const { targetCurrency, setTargetCurrency, config: toolbarResponse } = useToolbarContext();

  const handleChange = (_event: SyntheticEvent, value: string) => {
    setTargetCurrency(value);
  };

  return (
    <ToggleButtonGroup value={targetCurrency} exclusive onChange={handleChange}>
      {toolbarResponse.operatingCurrencies.map((currency) => (
        <ToggleButton key={currency} value={currency}>
          {currency}
        </ToggleButton>
      ))}
    </ToggleButtonGroup>
  );
}

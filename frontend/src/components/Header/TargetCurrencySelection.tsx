import { ToggleButton, ToggleButtonGroup } from "@mui/material";
import { useConfigContext } from "./ConfigProvider";
import { useToolbarContext } from "./ToolbarProvider";

export function TargetCurrencySelection() {
  const { config } = useConfigContext();
  const { targetCurrency, setTargetCurrency } = useToolbarContext();

  return (
    <ToggleButtonGroup
      value={targetCurrency}
      onChange={(_e, value) => {
        // MUI returns null when the active toggle is clicked again; ignore it to avoid writing ?currency=null
        if (value !== null) {
          setTargetCurrency(value);
        }
      }}
      exclusive
    >
      {config.operatingCurrencies.map((currency) => (
        <ToggleButton key={currency} value={currency}>
          {currency}
        </ToggleButton>
      ))}
    </ToggleButtonGroup>
  );
}

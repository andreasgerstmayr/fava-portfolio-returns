import CheckBoxIcon from "@mui/icons-material/CheckBox";
import CheckBoxOutlineBlankIcon from "@mui/icons-material/CheckBoxOutlineBlank";
import { Autocomplete, Checkbox, Chip, SxProps, TextField, useTheme } from "@mui/material";
import { amber, blue, grey, teal } from "@mui/material/colors";
import { SyntheticEvent } from "react";
import { useToolbarContext } from "./Header/ToolbarProvider";

export interface InvestmentOption {
  type: "Account" | "Group" | "Currency";
  id: string;
  /** text next to checkbox, and search text */
  label: string;
  chipLabel: string;
}

interface InvestmentsSelectionProps {
  label: string;
  types?: InvestmentOption["type"][];
  includeAllCurrencies?: boolean;
  investments: string[];
  setInvestments: (x: string[]) => void;
}

export function InvestmentsSelection(props: InvestmentsSelectionProps) {
  const { label, types, includeAllCurrencies, investments, setInvestments } = props;
  const { config } = useToolbarContext();
  const theme = useTheme();

  const options: InvestmentOption[] = [];
  if (!types || types.includes("Group")) {
    options.push(
      ...config.investmentsConfig.groups
        .map((x) => ({
          type: "Group" as const,
          id: x.id,
          label: x.name,
          chipLabel: x.name,
        }))
        .sort((a, b) => a.label.localeCompare(b.label)),
    );
  }
  if (!types || types.includes("Account")) {
    options.push(
      ...config.investmentsConfig.accounts
        .map((x) => ({
          type: "Account" as const,
          id: x.id,
          label: x.assetAccount,
          chipLabel: x.assetAccount,
        }))
        .sort((a, b) => a.label.localeCompare(b.label)),
    );
  }
  if (!types || types.includes("Currency")) {
    options.push(
      ...config.investmentsConfig.currencies
        .filter((x) => x.isInvestment || includeAllCurrencies)
        .map((x) => ({
          type: "Currency" as const,
          id: x.id,
          label: `${x.name} (${x.currency})`,
          chipLabel: x.currency,
        }))
        .sort((a, b) => a.label.localeCompare(b.label)),
    );
  }

  const option: InvestmentOption[] = investments
    .map((id) => options.find((x) => x.id === id))
    .filter((id) => id !== undefined);

  const handleChange = (_event: SyntheticEvent, value: InvestmentOption[]) => {
    setInvestments(value.map((i) => i.id));
  };

  const chipBackgroundColor = theme.palette.mode === "dark" ? "background.default" : grey[100];

  return (
    <Autocomplete
      multiple
      limitTags={2}
      disableCloseOnSelect
      value={option}
      onChange={handleChange}
      options={options}
      renderOption={(props, option, { selected }) => {
        // eslint-disable-next-line @typescript-eslint/no-unused-vars, react/prop-types
        const { key, ...otherProps } = props;
        return (
          <li key={option.id} {...otherProps}>
            <Checkbox
              icon={<CheckBoxOutlineBlankIcon fontSize="small" />}
              checkedIcon={<CheckBoxIcon fontSize="small" />}
              style={{ marginRight: 8 }}
              checked={selected}
            />
            <InvestmentChip type={option.type} sx={{ marginRight: 1 }} />
            {option.label}
          </li>
        );
      }}
      renderTags={(value: readonly InvestmentOption[], getTagProps) =>
        value.map((option: InvestmentOption, index: number) => {
          // eslint-disable-next-line @typescript-eslint/no-unused-vars
          const { key, ...tagProps } = getTagProps({ index });
          return (
            <Chip
              key={option.id}
              label={option.chipLabel}
              variant="outlined"
              sx={{ backgroundColor: chipBackgroundColor, border: `1px solid ${investmentColors[option.type]}` }}
              {...tagProps}
            />
          );
        })
      }
      style={{ width: 600 }}
      renderInput={(params) => <TextField {...params} label={label} className="investment-selection" />}
    />
  );
}

interface InvestmentChipProps {
  type: InvestmentOption["type"];
  sx?: SxProps;
}

function InvestmentChip({ type, sx }: InvestmentChipProps) {
  return (
    <Chip
      label={investmentAbbrs[type]}
      variant="outlined"
      size="small"
      sx={{ ...sx, color: investmentColors[type], borderColor: investmentColors[type] }}
    />
  );
}

const investmentAbbrs = {
  Account: "ACC",
  Group: "GRP",
  Currency: "CUR",
};

const investmentColors = {
  Account: blue[500],
  Group: teal[500],
  Currency: amber[500],
};

import CheckBoxIcon from "@mui/icons-material/CheckBox";
import CheckBoxOutlineBlankIcon from "@mui/icons-material/CheckBoxOutlineBlank";
import { Autocomplete, Checkbox, Chip, TextField, useTheme } from "@mui/material";
import { grey } from "@mui/material/colors";
import { SyntheticEvent } from "react";

interface PortfolioSelectionProps {
  label: string;
  /** all selectable portfolio names */
  options: string[];
  /** currently selected portfolio names */
  selected: string[];
  setSelected: (x: string[]) => void;
}

/**
 * Multi-select for filtering which portfolios are shown, styled like the
 * global "Investments Filter" (checkbox rows + outlined chips), but populated
 * with portfolio names from the asset-allocation config rather than accounts.
 */
export function PortfolioSelection({ label, options, selected, setSelected }: PortfolioSelectionProps) {
  const theme = useTheme();
  const chipBackgroundColor = theme.palette.mode === "dark" ? "background.default" : grey[100];

  const handleChange = (_event: SyntheticEvent, value: string[]) => {
    setSelected(value);
  };

  return (
    <Autocomplete
      multiple
      limitTags={4}
      disableCloseOnSelect
      value={selected}
      onChange={handleChange}
      options={options}
      renderOption={(props, option, { selected }) => {
        // eslint-disable-next-line react/prop-types
        const { key, ...optionProps } = props;
        return (
          <li key={key} {...optionProps}>
            <Checkbox
              icon={<CheckBoxOutlineBlankIcon fontSize="small" />}
              checkedIcon={<CheckBoxIcon fontSize="small" />}
              style={{ marginRight: 8 }}
              checked={selected}
            />
            {option}
          </li>
        );
      }}
      renderTags={(value: readonly string[], getTagProps) =>
        value.map((option: string, index: number) => {
          // eslint-disable-next-line @typescript-eslint/no-unused-vars
          const { key, ...tagProps } = getTagProps({ index });
          return (
            <Chip
              key={option}
              label={option}
              variant="outlined"
              sx={{ backgroundColor: chipBackgroundColor }}
              {...tagProps}
            />
          );
        })
      }
      style={{ width: 500 }}
      renderInput={(params) => <TextField {...params} label={label} />}
    />
  );
}

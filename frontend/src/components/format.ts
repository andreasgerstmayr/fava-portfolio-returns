// colors from fava
export const POSITIVE_NUMBER_COLOR = "#3daf46";
export const NEGATIVE_NUMBER_COLOR = "#af3d3d";

// colors from https://mui.com/material-ui/getting-started/templates/dashboard/
export const POSITIVE_TREND_COLOR = (opacity = 1) => `hsla(120, 44%, 53%, ${opacity})`;
export const NEGATIVE_TREND_COLOR = (opacity = 1) => `hsla(0, 90%, 40%, ${opacity})`;

export function getCurrencyFormatter(currency: string) {
  try {
    return new Intl.NumberFormat(undefined, {
      style: "currency",
      currency,
    }).format;
  } catch (_) {
    // currency code not found
    return (x: number | bigint) => `${x} ${currency}`;
  }
}

export function getIntegerCurrencyFormatter(currency: string) {
  try {
    return new Intl.NumberFormat(undefined, {
      style: "currency",
      currency,
      maximumFractionDigits: 0,
    }).format;
  } catch (_) {
    // currency code not found
    const fmt = new Intl.NumberFormat(undefined, {
      maximumFractionDigits: 0,
    }).format;
    return (x: number | bigint) => `${fmt(x)} ${currency}`;
  }
}

export const numberFormatter = new Intl.NumberFormat(undefined, {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
}).format;

export const percentFormatter = new Intl.NumberFormat(undefined, {
  style: "percent",
  maximumFractionDigits: 2,
}).format;

export const fixedPercentFormatter = new Intl.NumberFormat(undefined, {
  style: "percent",
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
}).format;

export function timestampToDate(ts: number) {
  const pad = (n: number) => n.toString().padStart(2, "0");
  const date = new Date(ts);
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`;
}

export function timestampToMonth(ts: number) {
  const pad = (n: number) => n.toString().padStart(2, "0");
  const date = new Date(ts);
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}`;
}

export const timestampToYear = (ts: number) => new Date(ts).getFullYear().toString();

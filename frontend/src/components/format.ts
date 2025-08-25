// Base colors from fava
const BASE_RED = '#af3d3d'
const BASE_GREEN = "#3daf46";

// colors from https://mui.com/material-ui/getting-started/templates/dashboard/
const BASE_GREEN_TREND = `120, 44%, 53%`;
const BASE_RED_TREND = `0, 90%, 40%`;

export interface PNLColorScheme {
  /** profit color */
  profit: string
  /** loss color */
  loss: string
  /** profit trend color */
  profitTrend: string
  /** loss trend color */
  lossTrend: string
}

export type PNLColorSchemeVariant = "green-red" |  "red-green"

export const PNL_COLOR_SCHEME: Record<PNLColorSchemeVariant, PNLColorScheme> =  {
  "green-red": {
    profit: BASE_GREEN,
    loss: BASE_RED,
    profitTrend: BASE_GREEN_TREND,
    lossTrend: BASE_RED_TREND,
  },
  "red-green": {
    profit: BASE_RED,
    loss: BASE_GREEN,
    profitTrend: BASE_RED_TREND,
    lossTrend: BASE_GREEN_TREND,
  }
}

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

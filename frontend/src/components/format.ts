// Base colors from fava
const BASE_POSITIVE_COLOR = "#3daf46";
const BASE_NEGATIVE_COLOR = "#af3d3d";

// Global configuration state
let globalSwapColors = false;

// Function to initialize color swapping based on config
export function initializeColorSwapping(swapColors: boolean) {
  globalSwapColors = swapColors;
}

// Dynamic color getters
export const getPositiveColor = () => globalSwapColors ? BASE_NEGATIVE_COLOR : BASE_POSITIVE_COLOR;
export const getNegativeColor = () => globalSwapColors ? BASE_POSITIVE_COLOR : BASE_NEGATIVE_COLOR;

// For backwards compatibility - these will be initialized later
export let POSITIVE_NUMBER_COLOR = BASE_POSITIVE_COLOR;
export let NEGATIVE_NUMBER_COLOR = BASE_NEGATIVE_COLOR;

// Update the exported constants when configuration changes
export function updateColors() {
  POSITIVE_NUMBER_COLOR = getPositiveColor();
  NEGATIVE_NUMBER_COLOR = getNegativeColor();
}

// colors from https://mui.com/material-ui/getting-started/templates/dashboard/
const BASE_POSITIVE_TREND_COLOR = (opacity = 1) => `hsla(120, 44%, 53%, ${opacity})`;
const BASE_NEGATIVE_TREND_COLOR = (opacity = 1) => `hsla(0, 90%, 40%, ${opacity})`;

export const POSITIVE_TREND_COLOR = (opacity = 1) =>
  globalSwapColors ? BASE_NEGATIVE_TREND_COLOR(opacity) : BASE_POSITIVE_TREND_COLOR(opacity);

export const NEGATIVE_TREND_COLOR = (opacity = 1) =>
  globalSwapColors ? BASE_POSITIVE_TREND_COLOR(opacity) : BASE_NEGATIVE_TREND_COLOR(opacity);

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

import { useConfigContext } from "./Header/ConfigProvider";

// convert locale from Fava/gettext (e.g. de_AT) to BCP 47 syntax (e.g. de-AT)
function toBcp47Locale(locale: string | null) {
  return locale ? locale.replace("_", "-") : undefined;
}

function useFormatter(opts: Intl.NumberFormatOptions) {
  const { config } = useConfigContext();
  const locale = toBcp47Locale(config.locale);
  return new Intl.NumberFormat(locale, opts).format;
}

export function useNumberFormatter() {
  return useFormatter({
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
}

export function usePercentFormatter(opts?: { fixed: boolean }) {
  return useFormatter({
    style: "percent",
    minimumFractionDigits: opts?.fixed ? 2 : undefined,
    maximumFractionDigits: 2,
  });
}

export function useCurrencyFormatter(currency: string, opts?: { integer: boolean }) {
  const { config } = useConfigContext();
  const locale = toBcp47Locale(config.locale);
  const maximumFractionDigits = opts?.integer ? 0 : undefined;

  try {
    return new Intl.NumberFormat(locale, {
      style: "currency",
      currency,
      maximumFractionDigits,
    }).format;
  } catch {
    // currency code not found
    const fmt = new Intl.NumberFormat(locale, {
      maximumFractionDigits,
    }).format;
    return (x: number | bigint) => `${fmt(x)} ${currency}`;
  }
}

export function anyFormatter(formatter: (value: number) => string) {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  return (value: any) => (typeof value === "number" ? formatter(value) : String(value));
}

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

export function getCurrencyFormatter(currency: string): (value: any) => string {
    try {
        return new Intl.NumberFormat(undefined, { style: "currency", currency }).format;
    } catch {
        return new Intl.NumberFormat().format;
    }
}

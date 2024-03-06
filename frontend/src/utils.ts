export function getCurrencyFormatter(currency: string) {
    // Handles the case where the currency is not supported by the Intl API
    // like stablecoins.
    const CURRENCY_MAPPER = {
        USDT: "USD",
        USDC: "USD",
        TUSD: "USD",
        BUSD: "USD",
        FDUSD: "USD",
        DAI: "USD",
        PYUSD: "USD",
        EURC: "EUR",
        EURT: "EUR",
    };
    currency = CURRENCY_MAPPER[currency] || currency;
    const currencyFormat = new Intl.NumberFormat(undefined, {
        style: "currency",
        currency,
    });
    return (value: any) => {
        return currencyFormat.format(value);
    };
}

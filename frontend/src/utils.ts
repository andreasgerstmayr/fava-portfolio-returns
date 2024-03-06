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
    try {
        const mapped = CURRENCY_MAPPER[currency];
        if (mapped) {
            console.warn(`Currency ${currency} is not supported by the Intl API, using ${mapped} instead`);
        }
        currency = mapped || currency;
        const currencyFormat = new Intl.NumberFormat(undefined, {
            style: "currency",
            currency,
        });
        return (value: any) => {
            return currencyFormat.format(value);
        };
    } catch (error) {
        console.error(`Currency ${currency} is not supported by the Intl API`, error);
        // Fallback to USD
        const currencyFormat = new Intl.NumberFormat(undefined, {
            style: "currency",
            currency: "USD",
        });
    }
}

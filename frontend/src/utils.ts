export function getCurrencyFormatter(currency: string) {
    const currencyFormat = new Intl.NumberFormat(undefined, {
        style: "currency",
        currency,
    });
    return (value: any) => {
        return currencyFormat.format(value);
    };
}

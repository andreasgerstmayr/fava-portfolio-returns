export function Help() {
  return (
    <div className="help-text">
      <h2>Calculating Portfolio Returns</h2>
      <p>fava-portfolio-returns supports multiple ways to calculate the portfolio performance.</p>

      <h3>Returns</h3>
      <p>
        Returns compares the market value with the cost value. In the Performance chart, the difference between the
        market value and the cost value is calculated per day. The values are aligned at 0%, to make them comparable
        with the performance of other groups and commodities.
      </p>

      <h3>Monetary Returns</h3>
      <p>
        Monetary returns computes the difference between the market value and the invested capital (sum of incoming and
        outgoing cash flows, including dividends and fees).
      </p>

      <h3>Internal Rate of Return (IRR)</h3>
      <p>Internal Rate of Return (IRR) accounts for the timing and magnitude of cash flows.</p>
      <p>
        For example, you invest 100 USD on the first day of January, and additional 20 USD on the first day of February.
        At the end of February, the investment is worth 200 USD. In other words, you invested 100 USD for two months (59
        days), and 20 USD for one month (28 days). IRR calculates <code>x</code> of the following formula:{" "}
        <code>100*(1+x)^(59/365) + 20*(1+x)^(28/365) = 200</code>.
      </p>
      <p>This method is recommended when you are in control of the cash flows.</p>

      <h3>Modified Dietz Method (MDM)</h3>
      <p>
        Modified Dietz Method (MDM) accounts for the timing and magnitude of cash flows. It approximates the Internal
        Rate of Return.
      </p>

      <h3>Time-Weighted Rate of Return (TWR)</h3>
      <p>Time-Weighted Return (TWR) eliminates the effects of cash flows. </p>
      <p>
        For example, you invest 100 USD in January. In June, your investment is worth 150 USD. The returns on this
        investment are 50% (<code>150/100-1</code>). Because of these returns, you decide to invest additional 100 USD.
        Now, the returns dropped to 25% (<code>250/200-1</code>), even though the price of the commodity did not change.
        The TWR eliminates this effect, which allows us to compare different portfolios without the effects of cash
        flows.
      </p>
      <p>This method is recommended for comparing two funds or portfolios.</p>
    </div>
  );
}

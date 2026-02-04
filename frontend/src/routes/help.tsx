import { createRoute, Link } from "@tanstack/react-router";
import { ReactNode } from "react";
import { Trans, useTranslation } from "react-i18next";
import { RootRoute } from "./__root";

export const HelpRoute = createRoute({
  getParentRoute: () => RootRoute,
  path: "help",
  staticData: {
    showInvestmentsSelection: false,
    showDateRangeSelection: false,
    showCurrencySelection: false,
  },
  component: Help,
});

interface Section {
  id: string;
  title: string;
  body: ReactNode;
  children?: Section[];
}

function Help() {
  const { t } = useTranslation();

  const sections: Section[] = [
    {
      id: "calculating-portfolio-returns",
      title: t("Calculating Portfolio Returns"),
      body: (
        <Trans>
          <p>fava-portfolio-returns supports multiple ways to calculate the portfolio performance.</p>
        </Trans>
      ),
      children: [
        {
          id: "returns",
          title: t("Returns"),
          body: (
            <Trans>
              <p>
                Returns compares the market value with the cost value. In the Performance chart, the difference between
                the market value and the cost value is calculated per day. The values are aligned at 0%, to make them
                comparable with the performance of other groups and commodities.
              </p>
            </Trans>
          ),
        },
        {
          id: "total-profit-and-loss",
          title: t("Total Profit and Loss"),
          body: (
            <Trans>
              <p>
                Total Profit and Loss computes the difference between the market value and the invested capital (sum of
                incoming and outgoing cash flows, including dividends and fees).
              </p>
            </Trans>
          ),
        },
        {
          id: "irr",
          title: t("Internal Rate of Return (IRR)"),
          body: (
            <Trans>
              <p>Internal Rate of Return (IRR) accounts for the timing and magnitude of cash flows.</p>
              <p>
                For example, you invest 100 USD on the first day of January, and additional 20 USD on the first day of
                February. At the end of February, the investment is worth 200 USD. In other words, you invested 100 USD
                for two months (59 days), and 20 USD for one month (28 days). IRR calculates <code>x</code> of the
                following formula: <code>100*(1+x)^(59/365) + 20*(1+x)^(28/365) = 200</code>.
              </p>
              <p>This method is recommended when you are in control of the cash flows.</p>
            </Trans>
          ),
        },
        {
          id: "mdm",
          title: t("Modified Dietz Method (MDM)"),
          body: (
            <Trans>
              <p>
                Modified Dietz Method (MDM) accounts for the timing and magnitude of cash flows. It approximates the
                Internal Rate of Return.
              </p>
            </Trans>
          ),
        },
        {
          id: "twr",
          title: t("Time-Weighted Rate of Return (TWR)"),
          body: (
            <Trans>
              <p>Time-Weighted Return (TWR) eliminates the effects of cash flows. </p>
              <p>
                For example, you invest 100 USD in January. In June, your investment is worth 150 USD. The returns on
                this investment are 50% (<code>150/100-1</code>). Because of these returns, you decide to invest
                additional 100 USD. Now, the returns dropped to 25% (<code>250/200-1</code>), even though the price of
                the commodity did not change. The TWR eliminates this effect, which allows us to compare different
                portfolios without the effects of cash flows.
              </p>
              <p>This method is recommended for comparing two funds or portfolios.</p>
            </Trans>
          ),
        },
      ],
    },
  ];

  const renderTOC = (level: number, sections: Section[]) => (
    <ul style={{ paddingLeft: `${level}em` }}>
      {sections.map((section) => (
        <li key={section.id} style={{ listStyle: "none" }}>
          <Link to="." hash={section.id}>
            {level == 0 ? <strong>{section.title}</strong> : section.title}
          </Link>
          {section.children && renderTOC(level + 1, section.children)}
        </li>
      ))}
    </ul>
  );

  const renderContent = (level: number, sections: Section[]) =>
    sections.map((section) => (
      <section key={section.id} aria-labelledby={section.id}>
        {level == 0 ? <h2 id={section.id}>{section.title}</h2> : <h3 id={section.id}>{section.title}</h3>}
        {section.body}
        {section.children && renderContent(level + 1, section.children)}
      </section>
    ));

  return (
    <div className="help-text">
      <nav aria-label={t("Table of contents")}>
        <h2>{t("Table of contents")}</h2>
        {renderTOC(0, sections)}
      </nav>

      {renderContent(0, sections)}
    </div>
  );
}

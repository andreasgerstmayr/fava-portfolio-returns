import { toMatchImageSnapshot } from "jest-image-snapshot";
import "jest-puppeteer";

const BASE_URL = "http://127.0.0.1:5000/beancount";
const tests = [
  { name: "Portfolio", url: "/extension/FavaPortfolioReturns/" },
  {
    name: "Performance",
    url: "/extension/FavaPortfolioReturns/?time=2021-2022#/performance?compareInvestments=c:VHT_c:GLD",
  },
  { name: "Returns", url: "/extension/FavaPortfolioReturns/#/returns" },
  { name: "Dividends", url: "/extension/FavaPortfolioReturns/#/dividends" },
  { name: "Cash Flows", url: "/extension/FavaPortfolioReturns/#/cash_flows?investments=c:VHT" },
  { name: "Groups", url: "/extension/FavaPortfolioReturns/#/groups" },
];

function customSnapshotIdentifier(p: { currentTestName: string }) {
  return p.currentTestName.replace("PNG Snapshot Tests ", "").replaceAll(" ", "_").toLowerCase();
}

expect.extend({ toMatchImageSnapshot });

describe("PNG Snapshot Tests", () => {
  beforeAll(async () => {
    await page.setUserAgent("puppeteer-png");
  });

  it.each(tests)(
    "$name",
    async ({ url }) => {
      await page.goto(`${BASE_URL}${url}`);
      await page.evaluate(() => {
        // full page screenshot doesn't work due to sticky sidebar
        document.body.style.height = "inherit";
      });
      await page.waitForNetworkIdle();

      const screenshot = await page.screenshot({ fullPage: true });
      expect(screenshot).toMatchImageSnapshot({ customSnapshotIdentifier });
    },
    10000,
  );
});

describe("HTML Snapshot Tests", () => {
  beforeAll(async () => {
    await page.setUserAgent("puppeteer-html");
  });

  it.each(tests)(
    "$name",
    async ({ url }) => {
      await page.goto(`${BASE_URL}${url}`);
      await page.waitForNetworkIdle();

      let html = await page.$eval("article", (element) => element.innerHTML);
      // remove nondeterministic rendering
      html = html.replaceAll(/_echarts_instance_="ec_[0-9]+"/g, "");
      html = html.replaceAll(/zr[0-9]+-[a-z][0-9]+/g, "zrX-cY");
      expect(html).toMatchSnapshot();
    },
    10000,
  );
});

import { toMatchImageSnapshot } from "jest-image-snapshot";
import "jest-puppeteer";

const BASE_URL = "http://127.0.0.1:5000/beancount/extension/FavaPortfolioReturns/";
const tests = [
  { name: "Portfolio", mode: "light", url: "" },
  { name: "Performance", mode: "light", url: "#/performance?compareWith=c:VHT_c:GLD" },
  { name: "Performance (TWR)", mode: "light", url: "#/performance?investments=g:Gold&method=twr&compareWith=c:GLD" },
  { name: "Returns", mode: "light", url: "#/returns" },
  { name: "Returns (MDM)", mode: "light", url: "#/returns?method=mdm" },
  { name: "Returns (TWR)", mode: "light", url: "#/returns?method=twr" },
  { name: "Dividends", mode: "light", url: "#/dividends" },
  { name: "Cash Flows", mode: "light", url: "#/cash_flows?investments=c:VHT" },
  { name: "Groups", mode: "light", url: "#/groups" },
  { name: "Investments", mode: "light", url: "#/investments" },
  { name: "Portfolio (dark)", mode: "dark", url: "" },
  { name: "Performance (dark)", mode: "dark", url: "#/performance?compareWith=c:VHT_c:GLD" },
  {
    name: "Performance (TWR) (dark)",
    mode: "dark",
    url: "#/performance?investments=g:Gold&method=twr&compareWith=c:GLD",
  },
  { name: "Returns (dark)", mode: "dark", url: "#/returns" },
  { name: "Returns (MDM) (dark)", mode: "dark", url: "#/returns?method=mdm" },
  { name: "Returns (TWR) (dark)", mode: "dark", url: "#/returns?method=twr" },
  { name: "Dividends (dark)", mode: "dark", url: "#/dividends" },
  { name: "Cash Flows (dark)", mode: "dark", url: "#/cash_flows?investments=c:VHT" },
  { name: "Groups (dark)", mode: "dark", url: "#/groups" },
  { name: "Investments (dark)", mode: "dark", url: "#/investments" },
];

function customSnapshotIdentifier(p: { currentTestName: string }) {
  return p.currentTestName
    .replace("PNG Snapshot Tests ", "")
    .replaceAll(/[^a-zA-Z ]/g, "")
    .replaceAll(" ", "_")
    .toLowerCase();
}

expect.extend({ toMatchImageSnapshot });

describe("PNG Snapshot Tests", () => {
  beforeAll(async () => {
    await page.setUserAgent("puppeteer-png");
  });

  it.each(tests)("$name", async ({ mode, url }) => {
    await page.emulateMediaFeatures([{ name: "prefers-color-scheme", value: mode }]);
    await page.goto(`${BASE_URL}${url}`);
    await page.evaluate(() => {
      // full page screenshot doesn't work due to sticky sidebar
      document.body.style.height = "inherit";
    });
    await page.waitForNetworkIdle();

    const screenshot = await page.screenshot({ fullPage: true });
    expect(Buffer.from(screenshot)).toMatchImageSnapshot({ customSnapshotIdentifier });
  });
});

describe("HTML Snapshot Tests", () => {
  beforeAll(async () => {
    await page.setUserAgent("puppeteer-html");
  });

  it.each(tests)("$name", async ({ url, mode }) => {
    await page.emulateMediaFeatures([{ name: "prefers-color-scheme", value: mode }]);
    await page.goto(`${BASE_URL}${url}`);
    await page.waitForNetworkIdle();

    let html = await page.$eval("article", (element) => element.innerHTML);
    // remove nondeterministic rendering
    html = html.replaceAll(/_echarts_instance_="ec_[0-9]+"/g, "");
    html = html.replaceAll(/zr[0-9]+-[a-z][0-9]+/g, "zrX-cY");
    expect(html).toMatchSnapshot();
  });
});

import { toMatchImageSnapshot } from "jest-image-snapshot";
import "jest-puppeteer";

const BASE_URL = "http://host.docker.internal:5000/beancount/extension/FavaPortfolioReturns/";
const tests = [
  { name: "Portfolio", url: "" },
  { name: "Performance", url: "#/performance?compareWith=c:VHT_c:GLD" },
  { name: "Performance (TWR)", url: "#/performance?investments=g:Gold&method=twr&compareWith=c:GLD" },
  { name: "Returns", url: "#/returns" },
  { name: "Returns (MDM)", url: "#/returns?method=mdm" },
  { name: "Returns (TWR)", url: "#/returns?method=twr" },
  { name: "Dividends", url: "#/dividends" },
  { name: "Cash Flows", url: "#/cash_flows?investments=c:VHT" },
  { name: "Groups", url: "#/groups" },
  { name: "Investments", url: "#/investments" },
];

function customSnapshotIdentifier(p: { currentTestName: string }) {
  let name = p.currentTestName
    .replace(/PNG Snapshot Tests (Light|Dark) Theme /, "")
    .replaceAll(/[^a-zA-Z ]/g, "")
    .replaceAll(" ", "_")
    .toLowerCase();
  if (p.currentTestName.includes("Dark")) {
    name += "_dark";
  }
  return name;
}

expect.extend({ toMatchImageSnapshot });

describe("PNG Snapshot Tests", () => {
  beforeAll(async () => {
    await page.setUserAgent("puppeteer-png");
  });

  describe("Light Theme", () => {
    it.each(tests)("$name", async ({ url }) => {
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

  describe("Dark Theme", () => {
    it.each(tests)("$name", async ({ url }) => {
      await page.emulateMediaFeatures([{ name: "prefers-color-scheme", value: "dark" }]);
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
});

describe("HTML Snapshot Tests", () => {
  beforeAll(async () => {
    await page.setUserAgent("puppeteer-html");
  });

  it.each(tests)("$name", async ({ url }) => {
    await page.goto(`${BASE_URL}${url}`);
    await page.waitForNetworkIdle();

    let html = await page.$eval("article", (element) => element.innerHTML);
    // remove nondeterministic rendering
    html = html.replaceAll(/_echarts_instance_="ec_[0-9]+"/g, "");
    html = html.replaceAll(/zr[0-9]+-[a-z][0-9]+/g, "zrX-cY");
    expect(html).toMatchSnapshot();
  });
});

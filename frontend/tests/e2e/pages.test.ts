import { expect, test } from "@playwright/test";

const BASE_URL = "http://127.0.0.1:5000/beancount/extension/FavaPortfolioReturns/";
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

test.describe("PNG Snapshot Tests", () => {
  test.describe("Light Theme", () => {
    tests.forEach(({ name, url }) => {
      test(name, async ({ page }) => {
        await page.goto(`${BASE_URL}${url}`);
        await expect(page).toHaveScreenshot();
      });
    });
  });

  test.describe("Dark Theme", () => {
    test.use({ colorScheme: "dark" });

    tests.forEach(({ name, url }) => {
      test(name, async ({ page }) => {
        await page.goto(`${BASE_URL}${url}`);
        await expect(page).toHaveScreenshot();
      });
    });
  });
});

test.describe("HTML Snapshot Tests", () => {
  tests.forEach(({ name, url }) => {
    test(name, async ({ page }) => {
      await page.goto(`${BASE_URL}${url}`);
      await expect(page.locator("body")).toMatchAriaSnapshot();
    });
  });
});

import { expect, Page, test } from "@playwright/test";

const BASE_URL = "http://127.0.0.1:5000/beancount/extension/FavaPortfolioReturns/";
const pages = [
  { name: "Portfolio", url: "" },
  { name: "Performance", url: "?path=performance&compareWith=c_VHT~c_GLD" },
  { name: "Performance (TWR)", url: "?path=performance&investments=g_Gold&metric=twr&compareWith=c_GLD" },
  { name: "Returns", url: "?path=returns" },
  { name: "Returns (MDM)", url: "?path=returns&metric=mdm" },
  { name: "Returns (TWR)", url: "?path=returns&metric=twr" },
  { name: "Dividends", url: "?path=dividends" },
  { name: "Cash Flows", url: "?path=cash_flows&investments=c_VHT" },
  { name: "Groups", url: "?path=groups" },
  { name: "Investments", url: "?path=investments" },
  { name: "Missing Prices", url: "?path=missing_prices" },
  { name: "Help", url: "?path=help" },
];

async function expectScreenshot(page: Page) {
  await page.evaluate(() => {
    // full page screenshot doesn't work due to sticky sidebar
    document.body.style.height = "inherit";
  });
  await page.waitForLoadState("networkidle");
  await expect(page.locator(".MuiCircularProgress-root")).toHaveCount(0);
  await expect(page.locator(".MuiSkeleton-root")).toHaveCount(0);
  await expect(page).toHaveScreenshot({ fullPage: true });
}

test.describe("PNG Snapshot Tests", () => {
  test.skip(!process.env.CONTAINER, "snapshot tests must run in a container");

  test.describe("Light Theme", () => {
    pages.forEach(({ name, url }) => {
      test(name, async ({ page }) => {
        await page.goto(`${BASE_URL}${url}`);
        await expectScreenshot(page);
      });
    });
  });

  test.describe("Dark Theme", () => {
    test.use({ colorScheme: "dark" });
    pages.forEach(({ name, url }) => {
      test(name, async ({ page }) => {
        await page.goto(`${BASE_URL}${url}`);
        await expectScreenshot(page);
      });
    });
  });
});

test.describe("HTML Snapshot Tests", () => {
  test.skip(!process.env.CONTAINER, "snapshot tests must run in a container");

  pages.forEach(({ name, url }) => {
    test(name, async ({ page }) => {
      await page.goto(`${BASE_URL}${url}`);
      await expect(page.locator("body")).toMatchAriaSnapshot();
    });
  });
});

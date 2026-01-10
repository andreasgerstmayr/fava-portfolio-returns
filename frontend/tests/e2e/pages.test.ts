import { expect, test } from "@playwright/test";

const BASE_URL = "http://127.0.0.1:5000/beancount/extension/FavaPortfolioReturns/";
const pages = [
  { name: "Portfolio", url: "" },
  { name: "Performance", url: "?path=performance&compareWith=c_VHT~c_GLD" },
  { name: "Performance (TWR)", url: "?path=performance&investments=g_Gold&method=twr&compareWith=c_GLD" },
  { name: "Returns", url: "?path=returns" },
  { name: "Returns (MDM)", url: "?path=returns&method=mdm" },
  { name: "Returns (TWR)", url: "?path=returns&method=twr" },
  { name: "Dividends", url: "?path=dividends" },
  { name: "Cash Flows", url: "?path=cash_flows&investments=c_VHT" },
  { name: "Groups", url: "?path=groups" },
  { name: "Investments", url: "?path=investments" },
];

test.describe("PNG Snapshot Tests", () => {
  test.describe("Light Theme", () => {
    pages.forEach(({ name, url }) => {
      test(name, async ({ page }) => {
        await page.goto(`${BASE_URL}${url}`);
        await page.evaluate(() => {
          // full page screenshot doesn't work due to sticky sidebar
          document.body.style.height = "inherit";
        });
        await expect(page).toHaveScreenshot({ fullPage: true });
      });
    });
  });

  test.describe("Dark Theme", () => {
    test.use({ colorScheme: "dark" });
    pages.forEach(({ name, url }) => {
      test(name, async ({ page }) => {
        await page.goto(`${BASE_URL}${url}`);
        await page.evaluate(() => {
          // full page screenshot doesn't work due to sticky sidebar
          document.body.style.height = "inherit";
        });
        await expect(page).toHaveScreenshot({ fullPage: true });
      });
    });
  });
});

test.describe("HTML Snapshot Tests", () => {
  pages.forEach(({ name, url }) => {
    test(name, async ({ page }) => {
      await page.goto(`${BASE_URL}${url}`);
      await expect(page.locator("body")).toMatchAriaSnapshot();
    });
  });
});

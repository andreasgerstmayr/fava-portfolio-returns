import { expect, test } from "@playwright/test";

const BASE_URL = "http://127.0.0.1:5000/beancount/extension/FavaPortfolioReturns/";

test("Portfolio page", async ({ page }) => {
  await page.goto(BASE_URL);
  await expect(page.locator("body")).toContainText(
    "The performance chart shows the total profit and loss of the portfolio",
  );
});

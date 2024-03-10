const { toMatchImageSnapshot } = require("jest-image-snapshot");
expect.extend({ toMatchImageSnapshot });

const waitFor = (ms) => new Promise((r) => setTimeout(r, ms));
const customSnapshotIdentifier = (p) =>
    p.currentTestName.replace(": PNG Snapshot Tests", "").replaceAll(" ", "_").toLowerCase();
const BASE_URL = "http://127.0.0.1:5000/beancount";
const dashboards = [
    { name: "Overview", link: "/extension/FavaPortfolioReturns/" },
    { name: "Gold", link: "/extension/FavaPortfolioReturns/?group=Gold" },
    { name: "VHT", link: "/extension/FavaPortfolioReturns/?group=Vanguard+Health+Care+ETF" },
    { name: "CORP", link: "/extension/FavaPortfolioReturns/?group=CORP" },
    { name: "CORP converted to EUR", link: "/extension/FavaPortfolioReturns/?group=CORP+(converted+to+EUR)" },
    { name: "CORPEUR", link: "/extension/FavaPortfolioReturns/?group=CORPEUR" },
    { name: "CORP June to August", link: "/extension/FavaPortfolioReturns/?group=CORP&time=2023-06+-+2023-08" },
];

describe("Report: PNG Snapshot Tests", () => {
    for (let dashboard of dashboards) {
        it(dashboard.name, async () => {
            await page.goto(`${BASE_URL}${dashboard.link}`);
            await page.evaluate(() => {
                // full page screenshot doesn't work due to sticky sidebar
                document.body.style.height = "inherit";
            });
            await waitFor(1500); // wait for animations to finish

            const screenshot = await page.screenshot({ fullPage: true });
            expect(screenshot).toMatchImageSnapshot({ customSnapshotIdentifier });
        });
    }
});

describe("Report: HTML Snapshot Tests", () => {
    for (let dashboard of dashboards) {
        it(dashboard.name, async () => {
            await page.setUserAgent("puppeteer");
            await page.goto(`${BASE_URL}${dashboard.link}`);
            await waitFor(1500); // wait for animations to finish

            let html = await page.$eval("article", (element) => element.innerHTML);
            // remove nondeterministic rendering
            html = html.replaceAll(/_echarts_instance_="ec_[0-9]+"/g, "");
            html = html.replaceAll(/zr[0-9]+-c[0-9]+/g, "zrX-cY");
            expect(html).toMatchSnapshot();
        });
    }
});

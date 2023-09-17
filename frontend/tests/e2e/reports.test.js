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
    { name: "CORPEUR", link: "/extension/FavaPortfolioReturns/?group=CORPEUR" },
    { name: "CORP June to August", link: "/extension/FavaPortfolioReturns/?group=CORP&time=2023-06+-+2023-08" },
];

describe("Report: PNG Snapshot Tests", () => {
    for (let dashboard of dashboards) {
        it(dashboard.name, async () => {
            await page.goto(`${BASE_URL}${dashboard.link}`);
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
            html = html.replaceAll(/_echarts_instance_="ec_[0-9]+"/g, "");

            // HACK: remove nondeterministic rendering
            html = html.replaceAll(/(?<=\.\d{9})\d+/g, ""); // ignore digits after 9th digit
            html = html.replaceAll(/y=".+?"/g, "");
            html = html.replaceAll(/transform="translate(.+?)"/g, "");
            html = html.replaceAll(/transform="matrix(.+?)"/g, "");
            html = html.replaceAll(/<path d=".+?"/g, "<path ");

            expect(html).toMatchSnapshot();
        });
    }
});

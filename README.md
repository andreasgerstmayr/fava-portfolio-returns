# Fava Portfolio Returns
[![Continuous Integration](https://github.com/andreasgerstmayr/fava-portfolio-returns/actions/workflows/continuous-integration.yaml/badge.svg)](https://github.com/andreasgerstmayr/fava-portfolio-returns/actions/workflows/continuous-integration.yaml)
[![PyPI](https://img.shields.io/pypi/v/fava-portfolio-returns)](https://pypi.org/project/fava-portfolio-returns/)

fava-portfolio-returns shows portfolio returns in the [Fava](https://github.com/beancount/fava) web interface. It leverages [beangrow](https://github.com/beancount/beangrow) to categorize transactions and calculate the portfolio returns of a beancount ledger.

[![Portfolio](https://github.com/andreasgerstmayr/fava-portfolio-returns/raw/main/frontend/tests/e2e/pages.test.ts-snapshots/PNG-Snapshot-Tests-Light-Theme-Portfolio-1-chromium-linux.png)](https://github.com/andreasgerstmayr/fava-portfolio-returns/raw/main/frontend/tests/e2e/pages.test.ts-snapshots/PNG-Snapshot-Tests-Light-Theme-Portfolio-1-chromium-linux.png)
[![Performance](https://github.com/andreasgerstmayr/fava-portfolio-returns/raw/main/frontend/tests/e2e/pages.test.ts-snapshots/PNG-Snapshot-Tests-Light-Theme-Performance-1-chromium-linux.png)](https://github.com/andreasgerstmayr/fava-portfolio-returns/raw/main/frontend/tests/e2e/pages.test.ts-snapshots/PNG-Snapshot-Tests-Light-Theme-Performance-1-chromium-linux.png)
[![Returns](https://github.com/andreasgerstmayr/fava-portfolio-returns/raw/main/frontend/tests/e2e/pages.test.ts-snapshots/PNG-Snapshot-Tests-Light-Theme-Returns-1-chromium-linux.png)](https://github.com/andreasgerstmayr/fava-portfolio-returns/raw/main/frontend/tests/e2e/pages.test.ts-snapshots/PNG-Snapshot-Tests-Light-Theme-Returns-1-chromium-linux.png)
[![Dividends](https://github.com/andreasgerstmayr/fava-portfolio-returns/raw/main/frontend/tests/e2e/pages.test.ts-snapshots/PNG-Snapshot-Tests-Light-Theme-Dividends-1-chromium-linux.png)](https://github.com/andreasgerstmayr/fava-portfolio-returns/raw/main/frontend/tests/e2e/pages.test.ts-snapshots/PNG-Snapshot-Tests-Light-Theme-Dividends-1-chromium-linux.png)
[![Cash Flows](https://github.com/andreasgerstmayr/fava-portfolio-returns/raw/main/frontend/tests/e2e/pages.test.ts-snapshots/PNG-Snapshot-Tests-Light-Theme-Cash-Flows-1-chromium-linux.png)](https://github.com/andreasgerstmayr/fava-portfolio-returns/raw/main/frontend/tests/e2e/pages.test.ts-snapshots/PNG-Snapshot-Tests-Light-Theme-Cash-Flows-1-chromium-linux.png)
[![Groups](https://github.com/andreasgerstmayr/fava-portfolio-returns/raw/main/frontend/tests/e2e/pages.test.ts-snapshots/PNG-Snapshot-Tests-Light-Theme-Groups-1-chromium-linux.png)](https://github.com/andreasgerstmayr/fava-portfolio-returns/raw/main/frontend/tests/e2e/pages.test.ts-snapshots/PNG-Snapshot-Tests-Light-Theme-Groups-1-chromium-linux.png)

## Installation
```
pip install fava-portfolio-returns
```

## Usage
Please setup [beangrow](https://github.com/beancount/beangrow) first, using this guide: https://beancount.github.io/docs/calculating_portolio_returns.html.

Enable this plugin in Fava by adding the following lines to your ledger:
```
2010-01-01 custom "fava-extension" "fava_portfolio_returns" "{
  'beangrow_config': 'beangrow.pbtxt'
}"
```

## Configuration
The plugin supports the following configuration options:
```
2010-01-01 custom "fava-extension" "fava_portfolio_returns" "{
  'beangrow_config': 'beangrow.pbtxt',
  'pnl_color_scheme': 'green-red',
  'beangrow_debug_dir': 'path/to/debug/directory'
}"
```

Available options for `pnl_color_scheme`:

- `green-red`: Green for profits, red for losses
- `red-green`: Red for profits, green for losses

The default value is automatically selected based on the browser's locale: Chinese and Japanese regions use `red-green` by default, all other regions use `green-red`.

## View Example Ledger
`cd example; fava example.beancount`

## Contributing
This plugin consists of a Python backend and a React frontend.

Install [uv](https://docs.astral.sh/uv/) and Node.js 22, run `make deps` to install the dependencies, and `make dev` to run the Fava dev server with auto-rebuild.

Before submitting a PR, please run `make build` to build the frontend in production mode, and add the compiled frontend to the PR.

## Related Projects
* [Fava Portfolio Summary](https://github.com/PhracturedBlue/fava-portfolio-summary)
* [Fava Classy Portfolio](https://github.com/seltzered/fava-classy-portfolio)
* [Fava Investor](https://github.com/redstreet/fava_investor)
* [Fava Dashboards](https://github.com/andreasgerstmayr/fava-dashboards)

## Acknowledgements
Thanks to Martin Blais and all contributors of [beancount](https://github.com/beancount/beancount) and [beangrow](https://github.com/beancount/beangrow),
Jakob Schnitzer, Dominik Aumayr and all contributors of [Fava](https://github.com/beancount/fava),
and to all contributors of [Apache ECharts](https://echarts.apache.org).

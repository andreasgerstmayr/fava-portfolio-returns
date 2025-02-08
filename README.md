# Fava Portfolio Returns
[![Continuous Integration](https://github.com/andreasgerstmayr/fava-portfolio-returns/actions/workflows/continuous-integration.yaml/badge.svg)](https://github.com/andreasgerstmayr/fava-portfolio-returns/actions/workflows/continuous-integration.yaml)
[![Open in Dev Containers](https://img.shields.io/static/v1?label=Dev%20Containers&message=Open&color=blue&logo=visualstudiocode)](https://vscode.dev/redirect?url=vscode://ms-vscode-remote.remote-containers/cloneInVolume?url=https://github.com/andreasgerstmayr/fava-portfolio-returns)

fava-portfolio-returns shows portfolio returns in the [Fava](https://github.com/beancount/fava) web interface. It leverages [beangrow](https://github.com/beancount/beangrow) to categorize transactions and calculate the portfolio returns of a beancount ledger.

[![Portfolio](frontend/tests/e2e/__image_snapshots__/portfolio.png)](frontend/tests/e2e/__image_snapshots__/portfolio.png)
[![Performance](frontend/tests/e2e/__image_snapshots__/performance.png)](frontend/tests/e2e/__image_snapshots__/performance.png)
[![Returns](frontend/tests/e2e/__image_snapshots__/returns.png)](frontend/tests/e2e/__image_snapshots__/returns.png)
[![Dividends](frontend/tests/e2e/__image_snapshots__/dividends.png)](frontend/tests/e2e/__image_snapshots__/dividends.png)
[![Cash Flows](frontend/tests/e2e/__image_snapshots__/cash_flows.png)](frontend/tests/e2e/__image_snapshots__/cash_flows.png)
[![Groups](frontend/tests/e2e/__image_snapshots__/groups.png)](frontend/tests/e2e/__image_snapshots__/groups.png)

## Installation
```
pip install git+https://github.com/andreasgerstmayr/fava-portfolio-returns.git
```

## Usage
Please setup [beangrow](https://github.com/beancount/beangrow) first, using this guide: https://beancount.github.io/docs/calculating_portolio_returns.html.

Enable this plugin in Fava by adding the following lines to your ledger:
```
2010-01-01 custom "fava-extension" "fava_portfolio_returns" "{
  'beangrow_config': 'beangrow.pbtxt',
}"
```

## View Example Ledger
`cd example; fava example.beancount`

## Building from Source
Run `make build-js` to compile the frontend. The compiled and bundled code will be placed in `src/fava_portfolio_returns/FavaPortfolioReturns.js`.

Run `make dev` to start a development server and automatically rebuild the frontend for any changes.

## Related Projects
* [Fava Portfolio Summary](https://github.com/PhracturedBlue/fava-portfolio-summary)
* [Fava Classy Portfolio](https://github.com/seltzered/fava-classy-portfolio)
* [Fava Investor](https://github.com/redstreet/fava_investor)
* [Fava Dashboards](https://github.com/andreasgerstmayr/fava-dashboards)

## Acknowledgements
Thanks to Martin Blais and all contributors of [beancount](https://github.com/beancount/beancount) and [beangrow](https://github.com/beancount/beangrow),
Jakob Schnitzer, Dominik Aumayr and all contributors of [Fava](https://github.com/beancount/fava),
and to all contributors of [Apache ECharts](https://echarts.apache.org).

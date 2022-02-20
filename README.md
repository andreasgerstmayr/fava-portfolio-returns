# fava-portfolio-returns
fava-portfolio-returns shows portfolio returns in the [Fava](https://github.com/beancount/fava) web interface. It leverages [beangrow](https://github.com/beancount/beangrow) to calculate the portfolio returns.

## Installation
```
pip install git+https://github.com/andreasgerstmayr/fava-portfolio-returns.git
```

## Usage
Please setup [beangrow](https://github.com/beancount/beangrow) first, using this guide: https://beancount.github.io/docs/calculating_portolio_returns.html.

Enable this plugin in Fava by adding the following lines to your ledger:
```
2010-01-0 custom "fava-extension" "fava_portfolio_returns" "{
  'beangrow_config': 'beangrow.pbtxt',
# 'beangrow_debug_dir': 'beangrow-debug/',
}"
```

## Building from Source
Run `make build` to compile the frontend. The compiled and bundled frontend will be placed in `fava_portfolio_returns/templates/PortfolioReturns.html`.

You can run `make watch` to automatically rebuild the frontend for any changes.

## Contributing
The goal of this Fava extension is to display beangrow reports in the browser.
Please implement any calculation changes or additions in the [beangrow](https://github.com/beancount/beangrow) repository, and any user interface changes to this repository.

## Acknowledgements
Thanks to Martin Blais and all contributors of [beancount](https://github.com/beancount/beancount) and [beangrow](https://github.com/beancount/beangrow),
Jakob Schnitzer, Dominik Aumayr and all contributors of [Fava](https://github.com/beancount/fava),
and to all contributors of [Apache ECharts](https://echarts.apache.org).

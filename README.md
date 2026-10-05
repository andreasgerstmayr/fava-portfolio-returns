# Fava Portfolio Returns
[![Continuous Integration](https://github.com/andreasgerstmayr/fava-portfolio-returns/actions/workflows/continuous-integration.yml/badge.svg)](https://github.com/andreasgerstmayr/fava-portfolio-returns/actions/workflows/continuous-integration.yml)
[![PyPI](https://img.shields.io/pypi/v/fava-portfolio-returns)](https://pypi.org/project/fava-portfolio-returns/)

fava-portfolio-returns shows portfolio returns in the [Fava](https://github.com/beancount/fava) web interface. It leverages [beangrow](https://github.com/beancount/beangrow) to categorize transactions and calculate the portfolio returns of a beancount ledger.

<a href="https://github.com/andreasgerstmayr/fava-portfolio-returns/raw/main/frontend/tests/e2e/snapshots.test.ts-snapshots/PNG-Snapshot-Tests-Light-Theme-Portfolio-1-chromium-linux.png">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://github.com/andreasgerstmayr/fava-portfolio-returns/raw/main/frontend/tests/e2e/snapshots.test.ts-snapshots/PNG-Snapshot-Tests-Dark-Theme-Portfolio-1-chromium-linux.png">
    <img alt="Portfolio" src="https://github.com/andreasgerstmayr/fava-portfolio-returns/raw/main/frontend/tests/e2e/snapshots.test.ts-snapshots/PNG-Snapshot-Tests-Light-Theme-Portfolio-1-chromium-linux.png">
  </picture>
</a>
<a href="https://github.com/andreasgerstmayr/fava-portfolio-returns/raw/main/frontend/tests/e2e/snapshots.test.ts-snapshots/PNG-Snapshot-Tests-Light-Theme-Performance-1-chromium-linux.png">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://github.com/andreasgerstmayr/fava-portfolio-returns/raw/main/frontend/tests/e2e/snapshots.test.ts-snapshots/PNG-Snapshot-Tests-Dark-Theme-Performance-1-chromium-linux.png">
    <img alt="Performance" src="https://github.com/andreasgerstmayr/fava-portfolio-returns/raw/main/frontend/tests/e2e/snapshots.test.ts-snapshots/PNG-Snapshot-Tests-Light-Theme-Performance-1-chromium-linux.png">
  </picture>
</a>
<a href="https://github.com/andreasgerstmayr/fava-portfolio-returns/raw/main/frontend/tests/e2e/snapshots.test.ts-snapshots/PNG-Snapshot-Tests-Light-Theme-Returns-1-chromium-linux.png">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://github.com/andreasgerstmayr/fava-portfolio-returns/raw/main/frontend/tests/e2e/snapshots.test.ts-snapshots/PNG-Snapshot-Tests-Dark-Theme-Returns-1-chromium-linux.png">
    <img alt="Returns" src="https://github.com/andreasgerstmayr/fava-portfolio-returns/raw/main/frontend/tests/e2e/snapshots.test.ts-snapshots/PNG-Snapshot-Tests-Light-Theme-Returns-1-chromium-linux.png">
  </picture>
</a>
<a href="https://github.com/andreasgerstmayr/fava-portfolio-returns/raw/main/frontend/tests/e2e/snapshots.test.ts-snapshots/PNG-Snapshot-Tests-Light-Theme-Dividends-1-chromium-linux.png">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://github.com/andreasgerstmayr/fava-portfolio-returns/raw/main/frontend/tests/e2e/snapshots.test.ts-snapshots/PNG-Snapshot-Tests-Dark-Theme-Dividends-1-chromium-linux.png">
    <img alt="Dividends" src="https://github.com/andreasgerstmayr/fava-portfolio-returns/raw/main/frontend/tests/e2e/snapshots.test.ts-snapshots/PNG-Snapshot-Tests-Light-Theme-Dividends-1-chromium-linux.png">
  </picture>
</a>
<a href="https://github.com/andreasgerstmayr/fava-portfolio-returns/raw/main/frontend/tests/e2e/snapshots.test.ts-snapshots/PNG-Snapshot-Tests-Light-Theme-Cash-Flows-1-chromium-linux.png">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://github.com/andreasgerstmayr/fava-portfolio-returns/raw/main/frontend/tests/e2e/snapshots.test.ts-snapshots/PNG-Snapshot-Tests-Dark-Theme-Cash-Flows-1-chromium-linux.png">
    <img alt="Cash Flows" src="https://github.com/andreasgerstmayr/fava-portfolio-returns/raw/main/frontend/tests/e2e/snapshots.test.ts-snapshots/PNG-Snapshot-Tests-Light-Theme-Cash-Flows-1-chromium-linux.png">
  </picture>
</a>
<a href="https://github.com/andreasgerstmayr/fava-portfolio-returns/raw/main/frontend/tests/e2e/snapshots.test.ts-snapshots/PNG-Snapshot-Tests-Light-Theme-Groups-1-chromium-linux.png">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://github.com/andreasgerstmayr/fava-portfolio-returns/raw/main/frontend/tests/e2e/snapshots.test.ts-snapshots/PNG-Snapshot-Tests-Dark-Theme-Groups-1-chromium-linux.png">
    <img alt="Groups" src="https://github.com/andreasgerstmayr/fava-portfolio-returns/raw/main/frontend/tests/e2e/snapshots.test.ts-snapshots/PNG-Snapshot-Tests-Light-Theme-Groups-1-chromium-linux.png">
  </picture>
</a>

[More screenshots](https://github.com/andreasgerstmayr/fava-portfolio-returns/tree/main/frontend/tests/e2e/snapshots.test.ts-snapshots)

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
  'beangrow_debug_dir': 'path/to/debug/directory',
  'pnl_color_scheme': 'green-red',
  'language': 'en',
  'locale': 'en',
}"
```

Available options for `pnl_color_scheme`:

- `green-red`: Green for profits, red for losses
- `red-green`: Red for profits, green for losses

The default value is automatically selected based on the browser's locale: Chinese and Japanese regions use `red-green` by default, all other regions use `green-red`.

### Asset Allocation and Rebalancing

The **Asset Allocation** tab compares the current allocation of one or more portfolios against a target allocation, and suggests how much to buy or sell to rebalance.
Targets can be set per commodity and/or per asset class.
Holdings are valued at the latest known prices (as of the end of the selected date range) in the selected currency.

The target allocation is read from a separate YAML file, so the same file can be shared with other tools (e.g., a CLI rebalancing script).
Point to it with the `asset_allocation_config` option:
```
2010-01-01 custom "fava-extension" "fava_portfolio_returns" "{
  'beangrow_config': 'beangrow.pbtxt',
  'asset_allocation_config': 'asset-allocation.yaml',
}"
```

Here is a complete example of what `asset-allocation.yaml` can contain (comments start with `#` and extend to the end of the line):
```yaml
# asset-class-key: asset-class  # commodity metadata key (default: asset-class)
# divergence-threshold:         # default divergence band (default: 5/25, below)
#   of-portfolio: 5%
#   of-target: 25%
portfolios:
  - name: Trading Portfolio
    accounts:
      - "Assets:Broker:Investments:"
    # divergence-threshold:     # optional; per-portfolio override
    #   of-portfolio: 3%
    allocation:                 # the target asset allocation, by...
      commodities:              # ... commodity, should sum to 100%
        - commodity: ETF_FOO
          target: 60%
          # divergence-threshold:   # optional; per-commodity (or class below) override
          #   of-target: 10%
        - commodity: ETF_BAR
          target: 40%
      classes:                  # ... asset class, should sum to 100%
        - asset-class: stocks
          target: 70%
        - asset-class: bonds
          target: 30%

# You can define more portfolios here:
#
# - name: Retirement Portfolio
#   accounts: ...
```

The following (nested) keys can be present in each portfolio definition:

- `name`: a human-readable unique identifier for the portfolio
- `accounts`: one or more account regexes (matched like Beanquery's `~` operator); all commodities held in any matching account are considered.
- `allocation`: the target asset allocation of the portfolio, defined by `commodities`, `classes`, or both; each block is shown as a separate sub-report.
- `allocation.commodities`: the target allocation per commodity; the targets should sum to 100%.
- `allocation.classes`: the target allocation per asset class. A commodity's asset class is read from its asset class metadata (see `asset-class-key` below); classes are hierarchical and `:`-separated, so a commodity with asset class `stocks:health` counts under a `stocks` (or `stocks:health`) target, choosing the most specific match. In the by-class report the rebalance suggestion is broken down into concrete per-commodity buy/sell trades.
- `asset-class-key` (optional, default `asset-class`): the commodity metadata key holding the asset class of a commodity.
- `divergence-threshold` (optional, default `min(5% of portfolio, 25% of target)`): the divergence band, i.e., how far a target may drift before it is highlighted for rebalancing, capped from two sides: `of-portfolio` in percentage points of the portfolio, `of-target` as a fraction of the target itself. The two thresholds are combined with `min()`, so a small sleeve is banded tightly without the large ones being held to the same absolute figure. The default is [Larry Swedroe's 5/25 rule](https://awealthofcommonsense.com/2014/03/larry-swedroe-525-rebalancing-rule/).

  A band can be set at the top level of the file, inside a portfolio (overriding it for that portfolio only) and on an individual commodity or asset-class target (overriding it, tighter or looser, for that target alone).

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

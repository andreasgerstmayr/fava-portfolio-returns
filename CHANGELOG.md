# Changelog

## v2.5.0 (2026-02-08)
* feat: internationalization support [#146](https://github.com/andreasgerstmayr/fava-portfolio-returns/pull/146) ([@andreasgerstmayr](https://github.com/andreasgerstmayr))
* feat: add annualized volatility metric [#156](https://github.com/andreasgerstmayr/fava-portfolio-returns/pull/156) ([@andreasgerstmayr](https://github.com/andreasgerstmayr))
* feat: add maximum drawdown (MDD) metric [#151](https://github.com/andreasgerstmayr/fava-portfolio-returns/pull/151) ([@andreasgerstmayr](https://github.com/andreasgerstmayr))
* feat: add metrics page, show series/rolling chart [#155](https://github.com/andreasgerstmayr/fava-portfolio-returns/pull/155) ([@andreasgerstmayr](https://github.com/andreasgerstmayr))
* feat: add TOC to help page [#152](https://github.com/andreasgerstmayr/fava-portfolio-returns/pull/152) ([@andreasgerstmayr](https://github.com/andreasgerstmayr))
* enhancement: rename "monetary returns" to "total profit and loss" [#150](https://github.com/andreasgerstmayr/fava-portfolio-returns/pull/150) ([@andreasgerstmayr](https://github.com/andreasgerstmayr))
* enhancement: perf chart: update series name [#149](https://github.com/andreasgerstmayr/fava-portfolio-returns/pull/149) ([@andreasgerstmayr](https://github.com/andreasgerstmayr))
* fix: compute unrealized P&L for time period [#148](https://github.com/andreasgerstmayr/fava-portfolio-returns/pull/148) ([@theaprilhare](https://github.com/theaprilhare))
* fix: add dependency on Beancount 3 [#141](https://github.com/andreasgerstmayr/fava-portfolio-returns/pull/141) ([@andreasgerstmayr](https://github.com/andreasgerstmayr))
* fix: fix whitespace and apply beangrow_mdm_zero_division.patch [#159](https://github.com/andreasgerstmayr/fava-portfolio-returns/pull/159) ([@jschuller](https://github.com/jschuller), [@theaprilhare](https://github.com/theaprilhare), [@andreasgerstmayr](https://github.com/andreasgerstmayr))
* fix: require two cashflows for IRR calculation [#160](https://github.com/andreasgerstmayr/fava-portfolio-returns/pull/160) ([@andreasgerstmayr](https://github.com/andreasgerstmayr))
* fix: fix links in portfolio allocation chart [#143](https://github.com/andreasgerstmayr/fava-portfolio-returns/pull/143) ([@andreasgerstmayr](https://github.com/andreasgerstmayr))

## v2.4.0 (2026-01-15)
* migrate to `@tanstack/router` and update URLs from `/beancount/extension/FavaPortfolioReturns/#/portfolio` to `/beancount/extension/FavaPortfolioReturns/?path=portfolio` [#134](https://github.com/andreasgerstmayr/fava-portfolio-returns/pull/134) ([@andreasgerstmayr](https://github.com/andreasgerstmayr))
* fix: add zero guard in MDM calculation [#136](https://github.com/andreasgerstmayr/fava-portfolio-returns/pull/136) ([@jschuller](https://github.com/jschuller))

## v2.3.0 (2026-01-01)
* visual updates for Performance page [#100](https://github.com/andreasgerstmayr/fava-portfolio-returns/pull/100) ([@Evernight](https://github.com/Evernight))
* add buy/sell points visualization to performance chart [#124](https://github.com/andreasgerstmayr/fava-portfolio-returns/pull/124) ([@val3344](https://github.com/val3344))
* fix beangrow_debug_dir option [#126](https://github.com/andreasgerstmayr/fava-portfolio-returns/pull/126) ([@andreasgerstmayr](https://github.com/andreasgerstmayr))
* dividends chart: hide legend if there are more than 10 investments [#131](https://github.com/andreasgerstmayr/fava-portfolio-returns/pull/131) ([@andreasgerstmayr](https://github.com/andreasgerstmayr))

## v2.2.0 (2025-12-03)
* update table design
* fix TWR calculation [#101](https://github.com/andreasgerstmayr/fava-portfolio-returns/pull/101) ([@Evernight](https://github.com/Evernight))
* fix annual interval calculations [#119](https://github.com/andreasgerstmayr/fava-portfolio-returns/pull/119) ([@val3344](https://github.com/val3344))
* use transaction date for market conversions [#96](https://github.com/andreasgerstmayr/fava-portfolio-returns/pull/96) ([@Evernight](https://github.com/Evernight))

## v2.1.0 (2025-10-14)
* publish releases to [PyPI](https://pypi.org/project/fava-portfolio-returns/)

## v2.0.0 (2025-01-26)
Rewrite of the plugin using React and Material UI with a REST API.

**New pages:**
* Portfolio: show portfolio performance, value and allocation
* Performance: compare performance with other groups and commodities
* Returns: show returns (IRR or TWR) in a heatmap, yearly and over periods
* Dividends: group dividends by stock and month/year

**New toolbar:**
* support investment selection based on defined groups, currencies and accounts.
* support selecting the operating currency
* support selecting predefined date ranges (3M/6M/YTD/1Y/3Y/5Y/MAX)

## v1.0.0 (2022-03-05)
* initial version

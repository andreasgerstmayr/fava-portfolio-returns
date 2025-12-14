# Changelog

## next
* add buy/sell points visualization to performance chart [#124](https://github.com/andreasgerstmayr/fava-portfolio-returns/pull/124) ([@val3344](https://github.com/val3344))

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

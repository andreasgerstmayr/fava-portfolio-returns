# This is a self-documenting Makefile, see https://www.thapaliya.com/en/writings/well-documented-makefiles/
default: help


##@ Build

node_modules: package.json yarn.lock
	yarn install

deps: node_modules  ## install dependencies

build: deps  ## build project
	yarn run build

watch: deps  ## watch and rebuild project
	yarn run watch

format: deps  ## format source
	yarn run format
	black --line-length 120 fava_portfolio_returns


##@ Helpers

help:  ## Display this help
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m\033[0m\n"} /^[a-zA-Z_-]+:.*?##/ { printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2 } /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) } ' $(MAKEFILE_LIST)

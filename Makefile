default: run

## Dependencies
deps-js:
	cd frontend; npm install

deps-js-update:
	cd frontend; npx npm-check-updates -i

deps-py:
	uv sync

deps-py-update:
	uv pip list --outdated
	uv lock --upgrade

deps: deps-js deps-py

vendor:
	uv run vendoring sync

## Build and Test
build-js:
	cd frontend; npm run build

build: build-js

test-py:
	uv run pytest

test-py-coverage:
	uv run coverage run -m pytest
	uv run coverage html

test-e2e:
	docker build -t fava-portfolio-returns-test -f Dockerfile.e2e .
	-docker rm -f fava-portfolio-returns-test
	docker run --name fava-portfolio-returns-test -e DISABLE_SNAPSHOT_TESTS fava-portfolio-returns-test || (rm -rf ./frontend/test-results && docker cp fava-portfolio-returns-test:/usr/src/app/frontend/test-results ./frontend && exit 1)

test-e2e-update:
	docker build -t fava-portfolio-returns-test -f Dockerfile.e2e .
	-docker rm -f fava-portfolio-returns-test
	-docker run --name fava-portfolio-returns-test fava-portfolio-returns-test --update-snapshots
	docker cp fava-portfolio-returns-test:/usr/src/app/frontend/tests/e2e/snapshots.test.ts-snapshots ./frontend/tests/e2e

test: test-py

## Utils
LEDGER_FILE ?= $(wildcard example/example.beancount src/fava_portfolio_returns/test/ledger/*.beancount)

run:
	uv run fava $(LEDGER_FILE)

# Development with live reload (parametrizable beancount file path)
# Usage: make dev LEDGER_FILE=path/to/file.beancount
dev:
	npx concurrently --names fava,esbuild \
	  "PYTHONUNBUFFERED=1 uv run fava --debug $(LEDGER_FILE)" \
	  "cd frontend; npm install && npm run watch"

beangrow:
	cd example; uv run beangrow-returns example.beancount beangrow.pbtxt reports

lint:
	cd frontend; npm run type-check
	cd frontend; npm run lint
	cd frontend; npm run lint:i18n
	uv run ty check
	uv run mypy src/fava_portfolio_returns scripts
	uv run pylint src/fava_portfolio_returns scripts

format:
	-cd frontend; npm run lint:fix
	cd frontend; npm run i18n
	-uv run ruff check --fix
	uv run ruff format .
	find example src/fava_portfolio_returns/test/ledger -name '*.beancount' -exec uv run bean-format -c 59 -o "{}" "{}" \;

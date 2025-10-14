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

test-js:
	cd frontend; LANG=en npm run test

test-js-update:
	cd frontend; LANG=en npm run test -- --update-snapshots

test-py:
	uv run pytest

test-py-coverage:
	uv run coverage run -m pytest
	uv run coverage html
	flatpak run org.chromium.Chromium htmlcov/index.html

test: test-py test-js

## Utils
run:
	cd example; uv run fava example.beancount

dev:
	npx concurrently --names fava,esbuild \
	  "PYTHONUNBUFFERED=1 uv run fava --debug example/*.beancount src/fava_portfolio_returns/test/ledger/*.beancount" \
	  "cd frontend; npm install && npm run watch"

dev-debug:
	npx concurrently --names fava,esbuild \
	  "PYTHONUNBUFFERED=1 LOGLEVEL=DEBUG uv run fava --debug example/*.beancount src/fava_portfolio_returns/test/ledger/*.beancount" \
	  "cd frontend; npm install && npm run watch"

beangrow:
	cd example; uv run beangrow-returns example.beancount beangrow.pbtxt reports

lint:
	cd frontend; npm run type-check
	cd frontend; npm run lint
	uv run mypy src/fava_portfolio_returns
	uv run pylint src/fava_portfolio_returns

format:
	-cd frontend; npm run lint:fix
	cd frontend; npx prettier -w ../src/fava_portfolio_returns/templates/*.css
	-uv run ruff check --fix
	uv run ruff format .
	find example src/fava_portfolio_returns/test/ledger -name '*.beancount' -exec uv run bean-format -c 59 -o "{}" "{}" \;

## Container
container-run: container-stop
	docker build -t fava-portfolio-returns-test -f Dockerfile.test .
	docker run -d --name fava-portfolio-returns-test fava-portfolio-returns-test
	docker exec fava-portfolio-returns-test curl --retry 10 --retry-connrefused --silent --output /dev/null http://127.0.0.1:5000

container-stop:
	docker rm -f fava-portfolio-returns-test

container-test: container-run
	docker exec fava-portfolio-returns-test make test || (rm -rf ./frontend/test-results && docker cp fava-portfolio-returns-test:/usr/src/app/frontend/test-results ./frontend && exit 1)
	make container-stop

container-test-js-update: container-run
	docker exec fava-portfolio-returns-test make test-js-update
	docker cp fava-portfolio-returns-test:/usr/src/app/frontend/tests/e2e/pages.test.ts-snapshots ./frontend/tests/e2e
	make container-stop

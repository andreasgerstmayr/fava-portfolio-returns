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

## Build and Test
build-js:
	cd frontend; npm run build

build: build-js

test-js:
	cd frontend; LANG=en npm run test

test-js-update:
	cd frontend; LANG=en npm run test -- -u

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
	npx concurrently --names fava,esbuild "cd example; PYTHONUNBUFFERED=1 uv run fava --debug --host 0.0.0.0 example.beancount" "cd frontend; npm run watch"

dev-debug:
	npx concurrently --names fava,esbuild "cd example; PYTHONUNBUFFERED=1 LOGLEVEL=DEBUG uv run fava --debug example.beancount" "cd frontend; npm run watch"

beangrow:
	cd example; uv run beangrow-returns example.beancount beangrow.pbtxt reports

lint:
	cd frontend; npx tsc --noEmit
	cd frontend; npm run lint
	uv run mypy src/fava_portfolio_returns
	uv run pylint src/fava_portfolio_returns

format:
	-cd frontend; npm run lint:fix
	cd frontend; npx prettier -w ../src/fava_portfolio_returns/templates/*.css
	-uv run ruff check --fix
	uv run ruff format .
	find example src/fava_portfolio_returns/test/ledger -name '*.beancount' -exec uv run bean-format -c 59 -o "{}" "{}" \;

ci:
	make lint
	make build
	make run &
	make test
	make format
	git diff --exit-code

## Container
start-browser: stop-browser
	docker run -d --name fava-portfolio-returns-test-browser -p 127.0.0.1:3000:3000 ghcr.io/browserless/chromium

stop-browser:
	docker rm -f fava-portfolio-returns-test-browser

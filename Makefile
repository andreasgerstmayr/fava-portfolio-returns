default: run

## Dependencies
deps-js:
	cd frontend; npm install && npx puppeteer browsers install chrome

deps-js-update:
	cd frontend; npx npm-check-updates -i

deps-py:
	rye sync

deps-py-update:
	rye lock --update-all

deps: deps-js deps-py

## Build and Test
build-js:
	cd frontend; npm run build

build: build-js

watch-js:
	cd frontend; npm run watch

test-js:
	cd frontend; LANG=en npm run test

test-js-update:
	cd frontend; LANG=en npm run test -- -u

test: test-js

## Utils
run:
	cd example; rye run fava example.beancount

run-debug:
	cd example; rye run fava --debug example.beancount

lint:
	cd frontend; npx tsc --noEmit
	rye run mypy src/fava_portfolio_returns/__init__.py
	rye run pylint src/fava_portfolio_returns/__init__.py

format:
	cd frontend; npx prettier -w . ../src/fava_portfolio_returns/templates/*.css
	rye run black src/fava_portfolio_returns/__init__.py
	find example -name '*.beancount' -exec rye run bean-format -c 59 -o "{}" "{}" \;

ci:
	make lint
	make build
	make run &
	make test

	make format
	git diff --exit-code

deps-js:
	cd frontend; npm install && npx puppeteer browsers install chrome

deps-py:
	cd example; pipenv install -d

deps: deps-js deps-py

build-js:
	cd frontend; npm run build

watch-js:
	cd frontend; npm run watch

test-js:
	cd frontend; LANG=en npm run test

test-js-update:
	cd frontend; LANG=en npm run test -- -u

run:
	cd example; pipenv run fava example.beancount

format:
	cd frontend; npx prettier -w . ../src/fava_portfolio_returns/templates/*.css
	cd example; pipenv run black ../src/fava_portfolio_returns/__init__.py
	cd example; find . -name '*.beancount' -exec pipenv run bean-format -c 59 -o "{}" "{}" \;

ci:
	make run &
	make test-js
	make format
	git diff --exit-code

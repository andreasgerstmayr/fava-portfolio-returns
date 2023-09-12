frontend/node_modules: frontend/package-lock.json
	cd frontend; npm install
	touch -m frontend/node_modules

.PHONY: build
build: frontend/node_modules
	cd frontend; npm run build

.PHONY: watch
watch: frontend/node_modules
	cd frontend; npm run watch

.PHONY: test
test: frontend/node_modules
	cd frontend; npm run test

.PHONY: format
format:
	prettier -w frontend src/fava_portfolio_returns/templates/*.css
	black src/fava_portfolio_returns/__init__.py
	find example -name '*.beancount' -exec bean-format -c 59 -o "{}" "{}" \;

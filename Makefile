build:
	cd frontend; npm run build

format:
	prettier -w frontend fava_portfolio_returns/templates/*.css
	black fava_portfolio_returns/__init__.py
	find . -name '*.beancount' -exec bean-format -c 59 -o "{}" "{}" \;

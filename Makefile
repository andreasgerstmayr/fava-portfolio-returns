build:
	cd frontend; npm run build

format:
	prettier -w frontend
	black fava_portfolio_returns/__init__.py

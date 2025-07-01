# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Fava extension for portfolio returns analysis that integrates with beancount ledgers. It's a full-stack application with a Python backend (Flask/Fava extension) and TypeScript/React frontend.

## Development Commands

### Frontend (from `frontend/` directory)
- `npm run build` - Build frontend for production
- `npm run watch` - Watch mode for development
- `npm run test` - Run Playwright e2e tests
- `npm run lint` - Run ESLint
- `npm run lint:fix` - Auto-fix ESLint issues

### Python Backend (from root directory)
- `uv run pytest` - Run Python tests
- `uv run mypy src/fava_portfolio_returns` - Type checking
- `uv run pylint src/fava_portfolio_returns` - Linting
- `uv run ruff check --fix` - Auto-fix code style
- `uv run ruff format .` - Format code

### Make Commands (from root directory)
- `make build` - Build entire project
- `make test` - Run all tests (Python + frontend)
- `make lint` - Run all linting/type checking
- `make format` - Format all code
- `make dev` - Start development server with hot reload
- `make run` - Run with example ledger

### Dependencies
- `make deps` - Install all dependencies
- `uv sync` - Sync Python dependencies
- `cd frontend; npm install` - Install frontend dependencies

## Architecture

### Backend (Python)
- **Main Extension**: `src/fava_portfolio_returns/__init__.py` - Flask extension that registers API endpoints
- **Core Logic**: `src/fava_portfolio_returns/core/` - Portfolio calculation and data processing
- **API Endpoints**: `src/fava_portfolio_returns/api/` - REST API handlers for different data views
- **Returns Calculation**: `src/fava_portfolio_returns/returns/` - Different return calculation methods (IRR, TWR, etc.)
- **Integration**: Uses beangrow library for portfolio categorization and calculation

### Frontend (TypeScript/React)
- **Entry Point**: `frontend/src/extension.ts` - Fava extension registration
- **App Root**: `frontend/src/app.tsx` - React app with routing and theming
- **Pages**: `frontend/src/pages/` - Main application views (Portfolio, Returns, etc.)
- **Components**: `frontend/src/components/` - Reusable UI components including chart components
- **API Layer**: `frontend/src/api/` - TypeScript API client for backend communication
- **State Management**: Uses @tanstack/react-query for server state
- **UI Library**: Material-UI components with custom theming
- **Charts**: Apache ECharts for data visualization

### Key Integrations
- **Fava Extension System**: Registers as a Fava plugin with custom endpoints
- **Beangrow**: External library for portfolio return calculations
- **Beancount**: Accounting data source and format

### Testing
- **Python**: pytest with coverage reporting
- **Frontend**: Playwright for e2e testing with visual regression tests
- **CI/CD**: GitHub Actions with containerized testing

### Configuration
- **beangrow.pbtxt**: Required configuration file for portfolio analysis
- **Extension Config**: Configured in beancount ledger with custom directive
- **Python**: Uses pyproject.toml for dependencies and tool configuration
- **Frontend**: Uses package.json and tsconfig.json

## Development Workflow

1. Backend changes: Edit Python files, run `make lint` and `make test-py`
2. Frontend changes: Edit TypeScript/React files, run `make build-js` and `make test-js`
3. Development server: Use `make dev` for hot reload of both frontend and backend
4. Full testing: Use `make test` to run complete test suite

## Important Notes

- Frontend is bundled into a single JS file that gets embedded in the Python package
- Extension integrates with existing Fava UI and follows its theming
- Requires properly configured beangrow setup for portfolio analysis
- Uses uv for Python dependency management instead of pip
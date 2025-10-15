.PHONY: install test lint format check-style run clean

# Variables
VENV = .venv
PYTHON = $(VENV)/bin/python
PIP = $(VENV)/bin/pip
UV = uv
PYTEST = $(VENV)/bin/pytest
BLACK = $(VENV)/bin/black
ISORT = $(VENV)/bin/isort
FLAKE8 = $(VENV)/bin/flake8
MYPY = $(VENV)/bin/mypy

# Default target
all: install

# Create virtual environment and install dependencies
install:
	@echo "Creating virtual environment..."
	$(UV) venv
	@echo "Installing dependencies..."
	$(UV) pip install -r requirements.txt
	$(UV) pip install -e ".[dev]"

# Run tests
test:
	$(PYTEST) tests/ -v --cov=app --cov-report=term-missing

# Run linter
lint:
	$(FLAKE8) app/

# Run type checker
type-check:
	$(MYPY) app/

# Format code
format:
	$(BLACK) app/
	$(ISORT) app/

# Check code style
check-style:
	$(BLACK) --check app/
	$(ISORT) --check-only app/

# Run the application
run:
	$(PYTHON) -m uvicorn app.main:app --reload

# Clean up
clean:
	rm -rf `find . -type d -name __pycache__`
	rm -rf .pytest_cache/ .mypy_cache/ .coverage htmlcov/

# Install pre-commit hooks
install-hooks:
	$(PIP) install pre-commit
	pre-commit install

# Run all checks
check: lint type-check test

# Help
help:
	@echo "Available commands:"
	@echo "  make install      Create virtual environment and install dependencies"
	@echo "  make test         Run tests"
	@echo "  make lint         Run linter"
	@echo "  make type-check   Run type checker"
	@echo "  make format       Format code"
	@echo "  make check-style  Check code style"
	@echo "  make run          Run the application"
	@echo "  make clean        Clean up"
	@echo "  make check        Run all checks (lint, type-check, test)"

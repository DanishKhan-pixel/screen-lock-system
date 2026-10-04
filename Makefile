.PHONY: help install migrate seed run test lint

VENV = .venv
PYTHON = $(VENV)/bin/python
PIP = $(VENV)/bin/pip
MANAGE = $(PYTHON) manage.py

help:          ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

install:       ## Create venv and install dependencies
	python3 -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt

migrate:       ## Run database migrations
	$(MANAGE) migrate

seed:          ## Load demo data
	$(MANAGE) seed_demo

run:           ## Start the development server
	$(MANAGE) runserver

test:          ## Run all tests
	$(MANAGE) test

lint:          ## Lint with ruff (install separately: pip install ruff)
	$(VENV)/bin/ruff check .

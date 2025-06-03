# Makefile for the cs (computer science) project
# This file contains commands for setting up the environment, formatting code,
# building the book, and other maintenance tasks.

.DEFAULT_GOAL := help

# Define all phony targets (targets that don't create files with the same name)
.PHONY: venv install fmt clean help test marimo

# Create a virtual environment using uv with Python 3.12
venv:
	curl -LsSf https://astral.sh/uv/install.sh | sh
	uv venv --python='3.12'

install: venv ## Install dependencies and setup environment
	uv pip install --upgrade pip
	uv pip install --no-cache-dir -r requirements.txt

fmt: venv ## Format and lint code
	uv pip install --no-cache-dir pre-commit
	uv run pre-commit install
	uv run pre-commit run --all-files

clean: ## Clean build artifacts and stale branches
	git clean -X -d -f
	git branch -v | grep "\[gone\]" | cut -f 3 -d ' ' | xargs git branch -D

help: ## Show this help message
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# Run marimo for interactive notebook development
marimo: ## Start a Marimo server
	@uv run pip instlal --no-cache-dir marimo
	@uv run marimo edit book/marimo  # Start marimo server in edit mode for the book/marimo directory

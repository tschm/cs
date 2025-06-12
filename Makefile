# Makefile for the cs (computer science) project
# This file contains commands for setting up the environment, formatting code,
# building the book, and other maintenance tasks.

.DEFAULT_GOAL := help

# Define all phony targets (targets that don't create files with the same name)
.PHONY: venv fmt clean help test marimo lint

# Create a virtual environment using uv with Python 3.12
uv:
	curl -LsSf https://astral.sh/uv/install.sh | sh

fmt: uv ## Format and lint code
	uvx pre-commit install
	uvx pre-commit run --all-files

ty: uv
	@uvx ty check book/marimo

lint: uv ## Run ruff linter and formatter
	@uvx ruff check --fix .
	@uvx ruff format .

clean: ## Clean build artifacts and stale branches
	git clean -X -d -f
	git branch -v | grep "\[gone\]" | cut -f 3 -d ' ' | xargs git branch -D

help: ## Show this help message
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# Run marimo for interactive notebook development
marimo: uv ## Start a Marimo server
	@uvx marimo edit --sandbox book/marimo/$(NOTEBOOK)  # Start marimo server in edit mode for the book/marimo directory

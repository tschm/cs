.DEFAULT_GOAL := help

.PHONY: venv install fmt clean help test jupyter book

venv:
	curl -LsSf https://astral.sh/uv/install.sh | sh
	uv venv

install: venv ## Install dependencies and setup environment
	uv pip install --upgrade pip
	uv pip install --no-cache-dir -r requirements.txt

fmt: venv ## Format and lint code
	uv pip install pre-commit
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



.PHONY: jupyter
jupyter: install ## Run jupyter lab
	uv pip install jupyterlab
	uv run jupyter lab

.PHONY: book
book: install  ## Compile the book
	uv pip install jupyterlab jupyter-book
	uv run jupyter-book clean book
	uv run jupyter-book build book

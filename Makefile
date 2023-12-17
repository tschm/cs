.DEFAULT_GOAL := help

SHELL=/bin/bash

VENV=.venv

.PHONY: install
install:  ## Install a virtual environment
	python -m venv ${VENV}
	${VENV}/bin/pip install --upgrade pip
	${VENV}/bin/pip install -r requirements.txt

.PHONY: fmt
fmt: install ## Run autoformatting and linting
	${VENV}/bin/pip install pre-commit
	${VENV}/bin/pre-commit install
	${VENV}/bin/pre-commit run --all-files

.PHONY: clean
clean:  ## Clean up caches and build artifacts
	@git clean -d -X -f

.PHONY: test
test: install ## Run tests
	.venv/bin/pip install pytest
	.venv/bin/pytest tests

.PHONY: help
help:  ## Display this help screen
	@echo -e "\033[1mAvailable commands:\033[0m"
	@grep -E '^[a-z.A-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}' | sort

.PHONY: jupyter
jupyter: install ## Run jupyter lab
	@.venv/bin/pip install jupyterlab
	@.venv/bin/jupyter lab

.PHONY: book
book: install  ## Compile the book
	@.venv/bin/pip install jupyterlab jupyter-book
	@.venv/bin/jupyter-book clean book
	@.venv/bin/jupyter-book build book

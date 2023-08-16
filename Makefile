.DEFAULT_GOAL := help

SHELL=/bin/bash

NAME="cs"

.PHONY: install
install:  ## Install a virtual environment
	python -m venv .venv
	.venv/bin/pip install -r requirements.txt
	.venv/bin/pip install pre-commit

.PHONY: kernel
kernel: install ## Create a kernel for jupyter lab
	.venv/bin/ipython kernel install --name=${NAME} --user

.PHONY: fmt
fmt:  install ## Run autoformatting and linting
	#.venv/bin/pip install pre-commit
	.venv/bin/pre-commit install
	.venv/bin/pre-commit run --all-files

.PHONY: clean
clean:  ## Clean up caches and build artifacts
	@git clean -d -X -f


.PHONY: help
help:  ## Display this help screen
	@echo -e "\033[1mAvailable commands:\033[0m"
	@grep -E '^[a-z.A-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}' | sort

.PHONY: jupyter
jupyter: ## Run jupyter lab
	@.venv/bin/jupyter lab

## Makefile (repo-owned)
# Keep this file small. It can be edited without breaking template sync.

LOGO_FILE=.rhiza/assets/rhiza-logo.svg

# Override template default: install the package editable so mkdocstrings can
# import it for API docs, and pull in the mkdocstrings plugin.
MKDOCS_EXTRA_PACKAGES = --with-editable . --with 'mkdocstrings[python]'

# Always include the Rhiza API (template-managed)
include .rhiza/rhiza.mk

# Optional: developer-local extensions (not committed)
-include local.mk

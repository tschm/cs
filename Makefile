## Makefile (repo-owned)
# Keep this file small. It can be edited without breaking template sync.

LOGO_FILE=.rhiza/assets/rhiza-logo.svg

# Override template default: install the package (non-editable) so mkdocstrings
# can import it for API docs, and pull in the mkdocstrings plugin. Use `--with .`
# rather than `--with-editable .` — the template enforces a no-editable policy in
# .rhiza/tests/integration/test_docs_targets.py (run by `make validate`).
MKDOCS_EXTRA_PACKAGES = --with . --with 'mkdocstrings[python]'

# Always include the Rhiza API (template-managed)
include .rhiza/rhiza.mk

# Optional: developer-local extensions (not committed)
-include local.mk

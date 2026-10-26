# SPDX-License-Identifier: Apache-2.0 OR MIT
.PHONY: check lint type test sec docs
check: lint type test docs
lint:
	poetry run ruff check pain001_mockbank tests scripts
	poetry run ruff format --check pain001_mockbank tests scripts
type:
	poetry run mypy pain001_mockbank
test:
	poetry run pytest
sec:
	poetry run bandit -q -r pain001_mockbank
	@# pip-audit installs only on Python 3.11+ (its filelock fix needs 3.11).
	@if poetry run python -c 'import sys; sys.exit(sys.version_info < (3, 11))'; then \
		poetry run pip-audit --progress-spinner off; \
	else \
		echo "pip-audit skipped: it needs Python 3.11+; the 3.14 job audits"; \
	fi
docs:
	poetry run python scripts/render_readme.py --check

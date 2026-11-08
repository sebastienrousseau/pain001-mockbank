# SPDX-License-Identifier: Apache-2.0 OR MIT
.PHONY: check lint type complexity test sec docs versions
check: lint type complexity test docs versions
lint:
	poetry run ruff check pain001_mockbank tests scripts
	poetry run ruff format --check pain001_mockbank tests scripts
type:
	poetry run mypy pain001_mockbank
complexity:
	poetry run python scripts/check_complexity.py
test:
	poetry run pytest
sec:
	poetry run bandit -q -r pain001_mockbank
	poetry run pip-audit --progress-spinner off
docs:
	poetry run python scripts/render_readme.py --check
versions:
	poetry run python scripts/verify_versions.py

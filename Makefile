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
	poetry run pip-audit --progress-spinner off
docs:
	poetry run python scripts/render_readme.py --check

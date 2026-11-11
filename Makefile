# SPDX-License-Identifier: Apache-2.0 OR MIT
.PHONY: check lint type complexity test sec docs versions demo
check: lint type complexity test docs versions
lint:
	poetry run ruff check pain001_mockbank tests scripts fuzz examples
	poetry run ruff format --check pain001_mockbank tests scripts fuzz examples
	poetry run ruff check --extend-select D pain001_mockbank examples
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
# Re-render the README demo (.github/demo.gif) from .github/demo.tape.
demo:
	@command -v vhs >/dev/null || { echo "install vhs: https://github.com/charmbracelet/vhs" >&2; exit 1; }
	PATH="$$(poetry env info -p)/bin:$$PATH" vhs .github/demo.tape

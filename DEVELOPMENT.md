<!-- SPDX-License-Identifier: Apache-2.0 OR MIT -->

# Development

Run `poetry install --all-extras`, then `poetry run make check` and
`poetry run make sec`. Tests require permission to bind localhost sockets.
They use synthetic data and ephemeral host keys, never a bank endpoint.
The coverage floor is 100% of package lines and branches.

CI checks Python 3.10 and 3.14, formatting, types, README generation and
security. The Dockerfile builds locally; recurring registry publication
requires separate explicit approval and is not enabled. Planned development
image tags are `edge` and immutable commit identifiers, not versioned releases.
Maintainers decide release versions.

Edit README evidence in `docs/readme-values.json`, then run
`poetry run python scripts/render_readme.py`. The layout in
`docs/readme-template.md` is vendored from the portfolio's canonical template;
do not change its structure locally.

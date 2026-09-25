# SPDX-License-Identifier: Apache-2.0 OR MIT
FROM python:3.12-slim@sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9 AS builder
WORKDIR /app
ENV POETRY_VIRTUALENVS_IN_PROJECT=true PIP_DISABLE_PIP_VERSION_CHECK=1
RUN pip install --no-cache-dir poetry==2.4.1
COPY pyproject.toml poetry.lock ./
RUN poetry install --only main --all-extras --no-root --no-interaction
COPY pain001_mockbank ./pain001_mockbank
RUN poetry install --only-root --no-interaction

FROM python:3.12-slim@sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9
LABEL org.opencontainers.image.source="https://github.com/sebastienrousseau/pain001-mockbank"
LABEL org.opencontainers.image.licenses="Apache-2.0 OR MIT"
RUN useradd --uid 10001 --create-home mockbank && mkdir /data && chown mockbank /data
WORKDIR /app
COPY --from=builder /app /app
COPY LICENSE LICENSE-APACHE LICENSE-MIT ./
USER 10001:10001
EXPOSE 2222 8080
ENTRYPOINT ["/app/.venv/bin/pain001-mockbank"]
CMD ["--host", "0.0.0.0", "--root", "/data"]

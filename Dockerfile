ARG PYTHON_IMAGE=python:3.12-slim
ARG UV_IMAGE=ghcr.io/astral-sh/uv:0.10.6
FROM ${UV_IMAGE} AS uv
FROM ${PYTHON_IMAGE}
COPY --from=uv /uv /uvx /usr/local/bin/
WORKDIR /service
COPY pyproject.toml uv.lock .python-version ./
RUN uv sync --locked --no-dev --no-cache
COPY app ./app
CMD ["uv", "run", "--locked", "--no-sync", "python", "-m", "app.main"]

# syntax=docker/dockerfile:1

FROM python:3.12-slim AS build

WORKDIR /app

RUN --mount=type=cache,target=/root/.cache/pip pip install poetry==2.1.2

RUN python3 -m venv .venv

COPY pyproject.toml poetry.lock /app/.

RUN --mount=type=cache,target=/root/.cache/pip \
    --mount=type=cache,target=/root/.cache/pypoetry/cache \
    POETRY_VIRTUALENVS_IN_PROJECT=True poetry install --without dev

FROM python:3.12-slim

WORKDIR /app

COPY --from=build /app/.venv /app/.venv

COPY --link ./app /app/

EXPOSE 5000

VOLUME /app/config.py

CMD ["/app/.venv/bin/waitress-serve", "--port=5000", "ccip:app"]


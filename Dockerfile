FROM python:3.13
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

COPY ./pyproject.toml /

COPY ./app /app
COPY ./docker-entrypoint.sh /app/docker-entrypoint.sh

EXPOSE 5000
WORKDIR /app
ENTRYPOINT ["bash", "docker-entrypoint.sh"]

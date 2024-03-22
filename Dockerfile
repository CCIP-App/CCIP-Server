FROM python:3.10

COPY ./pyproject.toml /

RUN curl -sSL https://install.python-poetry.org | python3 - && /root/.local/bin/poetry install

COPY ./app /app
COPY ./docker-entrypoint.sh /app/docker-entrypoint.sh

EXPOSE 5000
WORKDIR /app
ENTRYPOINT ["bash", "docker-entrypoint.sh"]

FROM python:3.10

COPY ./pyproject.toml /

RUN curl -sSL https://install.python-poetry.org | python3 - && /root/.local/bin/poetry install

COPY ./app /app

EXPOSE 5000
WORKDIR /app
ENTRYPOINT ["/root/.local/bin/poetry","run","waitress-serve", "--port=5000", "ccip:app"]

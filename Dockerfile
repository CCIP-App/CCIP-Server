FROM python:3.7

COPY ./Pipfile* /

RUN pip install --no-cache-dir pipenv && pipenv install

COPY ./app /app

EXPOSE 5000
WORKDIR /app
ENTRYPOINT ["pipenv","run","waitress-serve", "--port=5000", "ccip:app"]

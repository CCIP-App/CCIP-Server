FROM python:3.7
MAINTAINER Denny Huang

COPY ./Pipfile* /

RUN pip install --no-cache-dir pipenv && pipenv install

COPY ./app /app

EXPOSE 5000
WORKDIR /app
ENV FLASK_APP ccip.py
CMD ["pipenv", "run", "flask", "run", "--host=0.0.0.0"]

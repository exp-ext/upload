FROM python:3.11-alpine

WORKDIR /server

RUN apk add --no-cache \
    postgresql-client

COPY requirements.txt ./

RUN pip3 install -r requirements.txt

COPY . .

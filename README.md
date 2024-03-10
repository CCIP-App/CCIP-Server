# CCIP-Server

A Community Checkin with Interactivity Project Server

## Pre-Requirement & run

Read `Dockerfile`

## Run CCIP-Server with Docker

- Make sure `docker` and `make` are installed.
- Execute the follwoing commands every time you change the `config`, `json` or `csv` files.

```bash
make go
```

You should get the following messages if it works.

```
ccip_server  | INFO:waitress:Serving on http://0.0.0.0:5000
```

## Get into the running CCIP-Server container instance

```bash
make shell
```

# AGENTS.md

This repository is `CCIP-App/CCIP-Server`, the event-side API server for
OPass. Read this file before changing code so you keep the public OPass product
model, the event deployment model, and the local Python service boundaries
straight.

## Public Project Context

OPass is a shared open-source event check-in and event-information platform for
Taiwan FLOSS conferences. The public site describes it as a way to check in,
plan schedules, and receive announcements; it has repeatedly been used by
SITCON, COSCUP, PyCon TW, g0v summit, HITCON, and related community events.

Useful public references:

- https://opass.app/ - product overview and GitHub org link.
- https://hackmd.io/@OPass/rJitRr3VS - OPass architecture and API flow.
- https://hackmd.io/@OPass/booth - puzzle / gamification operating model.
- https://github.com/CCIP-App/ - OPass source organization.
- https://github.com/CCIP-App/Portal - event list and event-detail
  configuration source.
- https://github.com/CCIP-App/schedule-json-generator - schedule JSON source
  pipeline mentioned by the architecture note.

Mental model:

- `Portal` publishes the list of available events and each event's static
  detail JSON. The mobile apps discover an event there.
- The event detail JSON can include `server_base_url`; that URL points at a
  deployment of this repository.
- This server handles attendee token status, scenario usage, announcements,
  dashboards, and puzzle/gamification endpoints.
- Schedules are outside this server. They come from the event's `schedule_url`.
- Puzzle frontends are separate projects. This server stores identity, puzzle
  buckets, delivery permissions, status, and dashboards.

## Repository Shape

- `app/ccip.py` is the Flask app and all HTTP routes.
- `app/import.py` imports attendee CSV rows into MongoDB and binds scenarios.
- `app/models/` contains MongoEngine documents:
  - `Attendee` and embedded `Scenario`
  - `Announcement`
  - `PuzzleStatus` and `PuzzleBucket`
- `app/config-sample.py` documents the runtime `config.py` shape.
- `app/*-sample.*` files are fixtures or examples only.
- `Dockerfile`, `docker-compose.yml`, and `Makefile` are the main deployment
  path.
- `pyproject.toml` uses `uv`; runtime dependencies are Flask, MongoEngine, and
  Waitress. The dev dependency group currently only contains Flake8.

There are no tests in the repository at the time this file was written.

## Runtime Configuration And Data

This service is configured by files inside `app/` at container runtime. Several
of them are intentionally ignored by git because they are event-specific:

- `config.py`
- `scenario*.json`
- `puzzle-config.json`
- `delivery-permission.json`
- `reg.csv`

Do not commit real event config, attendee CSVs, QR-code tokens, deliverer tokens,
or MongoDB connection secrets.

`config.py` must define:

- `MONGODB_SETTINGS`, passed to `mongoengine.connect`.
- `SCENARIO_DEFS`, mapping a role such as `audience` or `staff` to a scenario
  definition JSON filename.
- `ANNOUNCEMENT_DEFAULT_ROLE`, used when `/announcement` is called without a
  valid attendee token.

Scenario definition JSON is loaded on process start. Historical sample shape
includes keys like:

- `order`
- `display_text`
- `available_time` and `expire_time`, parsed as `%Y/%m/%d %H:%M %z`
- `countdown`
- `lock_message`
- `not_lock_rule`
- `show_rule`
- `attr`
- `related_scenario`
- `deliver_puzzle`

If you change scenario semantics, update both `app/import.py` and
`app/ccip.py`; import-time binding and request-time usage are split.

## Important API Behavior

Attendee identity:

- Most attendee endpoints take `?token=<private attendee token>`.
- `Attendee.public_token` is `sha1(token)` and is used for puzzle sharing.
- `/status` records `first_use` and initializes the attendee's puzzle bucket on
  first normal access. Passing `StaffQuery` changes that behavior.
- `/use/<scenario_id>` consumes a scenario, may unlock or disable related
  scenarios, may mark related scenarios used for staff scans, and may deliver
  puzzle pieces.

Puzzle endpoints:

- `/event/puzzle?token=<public_token>` reads a puzzle bucket.
- `/event/puzzle/revoke?token=<private attendee token>` invalidates the bucket
  and decrements current puzzle currency counters.
- `/event/puzzle/coupon?token=<private attendee token>` marks coupon use.
- `/event/puzzle/deliverer?token=<deliverer token>` maps a delivery token to a
  delivery slug from `delivery-permission.json`.
- `/event/puzzle/deliverers` lists delivery slugs.
- `POST /event/puzzle/deliver?token=<deliverer token>` expects form
  `receiver=<private attendee token>` and delivers one puzzle piece.
- `/event/puzzle/dashboard` returns puzzle counters.

Announcements and dashboards:

- `GET /announcement` returns announcements for the attendee role if a valid
  token is provided; otherwise it uses `ANNOUNCEMENT_DEFAULT_ROLE`.
- `POST /announcement` creates an announcement from form fields `msg_zh`,
  `msg_en`, `uri`, and `role[]`. There is no in-repo auth guard, so deployments
  must protect this endpoint externally if needed.
- `/dashboard`, `/dashboard/<role>`, `/roles`, and `/scenarios?role=...` expose
  operational state.

## Local Commands

Use the repository's `uv` setup for Python work:

```bash
uv sync
uv run flake8 app
```

Run the service the same way the README describes:

```bash
make go
```

The expected successful container log includes Waitress serving on port 5000.
Use:

```bash
make shell
```

to enter the running `backend` container.

To import attendees, run from `app/` or make sure relative config/scenario paths
resolve the same way they do in the container:

```bash
EVENT_ID=<event-id> uv run python import.py reg.csv audience
EVENT_ID=<event-id> uv run python import.py staff.csv staff
```

`app/import.py` requires `EVENT_ID` in the environment and a role that exists in
`SCENARIO_DEFS`.

## Development Guidance

- Keep changes small and explicit; this is a compact service with global
  module-load state.
- Be careful with process-start side effects. `app/ccip.py` reads config and
  optional puzzle files during import, and initializes `PuzzleStatus` when
  puzzle config exists.
- Avoid importing the Flask app in ad hoc scripts unless the expected
  `config.py`, scenario files, optional puzzle files, and MongoDB are available.
- Preserve API compatibility with the mobile apps, Portal event config, and
  separate puzzle frontends. Existing endpoints are simple but externally
  coupled.
- Treat query parameter names and form field names as public contracts.
- When touching token or attendee flows, distinguish private attendee `token`,
  public SHA-1 `public_token`, and deliverer permission token.
- If you add tests later, prefer focused Flask test-client coverage around
  route behavior and MongoEngine model state. Consider `mongomock` or a test
  MongoDB fixture instead of real event data.
- Validate JSON and CSV fixture changes separately from Python linting.
- Do not modernize `app/webhook.sh` casually. It is legacy KKTIX import tooling
  and includes environment-specific assumptions.

## Before You Finish

At minimum, run the cheapest applicable validation:

```bash
uv run flake8 app
```

If you touched Docker, run or explicitly report why you could not run:

```bash
make build
```

If you touched route behavior, exercise the relevant endpoint against a local
container or Flask test client with non-real sample data.

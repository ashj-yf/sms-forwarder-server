# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Common commands

### Backend setup and run

```bash
uv sync --extra dev
cp .env.example .env
uv run alembic upgrade head
uv run python -m app.cli.create_admin admin secret123
uv run uvicorn app.main:app --reload --port 8000
```

Health check:

```bash
curl http://localhost:8000/api/v1/healthz
```

### Backend checks and tests

```bash
uv run ruff check app tests
uv run python -m compileall app tests
uv run pytest
```

Run a single test file or test case:

```bash
uv run pytest tests/test_api_flow.py
uv run pytest tests/test_api_flow.py::test_api_flow
```

### Database migrations

```bash
uv run alembic upgrade head
uv run alembic revision --autogenerate -m "message"
```

Migrations live under `app/db/migrations/versions/` and are configured by `alembic.ini` plus `app/db/migrations/env.py`.

### Frontend development

The React SPA lives in `frontend/`. During development Vite proxies `/api` to the backend on port 8000.

```bash
cd frontend
npm install
npm run dev
```

Frontend production build and typecheck:

```bash
cd frontend
npm run build
npm run typecheck
```

The build output is `frontend/dist`. If this directory exists, `app/main.py` serves it at `/` while `/api/v1/*` remains handled by FastAPI.

### Docker

```bash
docker build -t sms-forwarder-server:local .
docker compose up --build
```

The Dockerfile uses build args for the base images and currently defaults to the `docker.1ms.run` mirror:

```bash
docker build \
  --build-arg NODE_IMAGE=docker.1ms.run/library/node:22-slim \
  --build-arg PYTHON_IMAGE=docker.1ms.run/library/python:3.13-slim \
  -t sms-forwarder-server:local .
```

## High-level architecture

This repository is a FastAPI backend plus a React SPA console for SmsForwarder device management. The backend is the source of truth for authentication, devices, webhook ingestion, cached events, and realtime proxy calls to SmsForwarder devices.

### Request/response shape

All API routes are mounted under `/api/v1` from `app/main.py` through `app/api/v1/router.py`. Success and error responses use a common envelope from `app/utils/responses.py`:

- success: `{ code, msg, data, request_id, timestamp }`
- error: `{ code, msg, data, request_id, timestamp }`

`app/main.py` installs request-id middleware. It accepts `X-Request-ID` if provided, otherwise generates one, and echoes it in the response header. Keep this envelope and request-id behavior in mind when adding API endpoints or frontend client calls.

### Backend layers

- `app/api/v1/` contains route modules. Routes are thin: they validate schemas, inject DB/current user dependencies, check permissions, and call services.
- `app/schemas/` contains Pydantic request/response contracts. Frontend types in `frontend/src/api/types.ts` mirror these contracts manually.
- `app/services/` contains business logic:
  - `auth_service.py` handles login and JWT subject lookup.
  - `device_service.py` handles device create/update/list/get.
  - `webhook_service.py` handles webhook token lifecycle and webhook event ingestion.
  - `command_service.py` handles `mode=realtime` vs `mode=cache` query dispatch.
  - `audit_service.py` records server-side audit events where used.
- `app/models/` contains SQLAlchemy models. Device data and webhook events are persisted here.
- `app/adapters/` contains integration boundaries, especially `SmsForwarderHttpAdapter` for forwarding realtime requests to the device HTTP API and `webhook_parser.py` for normalizing inbound webhook payloads.
- `app/utils/` contains shared helpers for crypto, id generation, masking, rate limiting, deduplication, and response envelopes.

### Auth and permissions

Authentication uses JWT Bearer tokens. Login is `POST /api/v1/auth/login`; current user lookup is `GET /api/v1/auth/me`. Permission checks are enforced by dependencies in `app/api/deps.py`; `admin:*` is treated as a wildcard permission. The frontend should treat backend 403 responses as authoritative because `/auth/me` currently returns user identity only, not a permission list.

### Device query model

Most resource queries are POST endpoints under `/api/v1/devices/{device_id}/.../query`:

- `sms/query`
- `calls/query`
- `contacts/query`
- `battery/query`
- `location/query`
- `config/query`

`app/services/command_service.py` is the central dispatch point. `mode=realtime` forwards to the SmsForwarder device through `SmsForwarderHttpAdapter`; it requires a device `base_url` and fails for `channel_type == "webhook_only"`. `mode=cache` reads previously ingested webhook events from `device_events`. SMS, calls, and contacts support pagination fields; battery, location, and config only use `mode`.

### Webhook model

Authenticated operators create or rotate webhook tokens through `/api/v1/devices/{device_id}/webhook`. SmsForwarder devices post public inbound events to `/api/v1/webhooks/smsforwarder/{webhook_token}`. The plaintext token is only available when created or rotated; backend storage uses a hash. Do not design UI or APIs that assume the token can be read back later.

### Frontend architecture

The SPA is in `frontend/` and uses Vite, React, TypeScript, React Router, TanStack Query, and the Fetch API wrapper in `frontend/src/api/client.ts`.

Important frontend conventions:

- `frontend/src/api/client.ts` is the single API transport layer. It injects Bearer token and `X-Request-ID`, unwraps the backend envelope, and converts non-2xx/error envelopes into `ApiError`.
- `frontend/src/store/auth.ts` stores the token in `sessionStorage`.
- Endpoint wrappers are grouped under `frontend/src/api/endpoints/` by backend domain.
- `frontend/src/App.tsx` currently contains the route tree and page components for the console.
- `frontend/src/styles/globals.css` defines the dark operator-console visual system.

### Static hosting

`app/main.py` checks for `frontend/dist`. When present, it mounts `/assets` and registers a catch-all route that returns `frontend/dist/index.html`. Keep the API router registration before the SPA fallback so `/api/v1/*` is never intercepted by the frontend route.

### Configuration

Runtime settings are defined in `app/core/config.py` and read from `.env` via Pydantic settings. Key settings include `DATABASE_URL`, `PUBLIC_BASE_URL`, `JWT_SECRET`, `APP_SECRET`, token expiry, HTTP timeout, and rate limits. SQLite is the default development database; PostgreSQL can be selected with `DATABASE_URL`.

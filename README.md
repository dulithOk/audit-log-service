# Audit Log Service

A production-grade, reusable audit logging microservice built with **FastAPI**, **PostgreSQL**, **SQLAlchemy (async)**, and **Alembic**. Any internal service can integrate via API key to write and query structured audit events.

---

## Architecture

```
app/
├── config/         # Settings (pydantic-settings), DB engine, logging
├── controller/     # FastAPI routers (HTTP layer only)
├── service/        # Business logic
├── repository/     # DB queries via SQLAlchemy async
├── models/         # ORM models
├── schemas/        # Pydantic request/response schemas
├── middleware/      # API key auth, request ID injection
└── exceptions/     # Typed domain exceptions
alembic/            # Database migrations
scripts/            # DB init SQL
```

---

## Quick Start

### 1. Configure environment

```bash
cp .env.example .env
# Fill in DB_HOST, DB_NAME, DB_USER, DB_PASSWORD, API_KEYS
```

### 2. Run with Docker Compose

```bash
docker compose up -d
```

Migrations run automatically on container start.

### 3. Run locally

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

---

## Database Migrations

```bash
# Generate a new migration after model changes
alembic revision --autogenerate -m "describe change"

# Apply all pending migrations
alembic upgrade head

# Roll back one migration
alembic downgrade -1
```

Alembic reads **individual DB config fields** (`DB_HOST`, `DB_PORT`, etc.) from `.env` via `app/config/settings.py`. There is no raw `DATABASE_URL` env var.

---

## API Reference

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/v1/audit-logs/` | Create a single log entry |
| `POST` | `/api/v1/audit-logs/bulk` | Bulk-create up to 1 000 entries |
| `GET` | `/api/v1/audit-logs/` | List & filter logs (paginated) |
| `GET` | `/api/v1/audit-logs/{id}` | Fetch one entry by UUID |
| `GET` | `/health` | Health check (DB connectivity) |

### Authentication

Pass your API key in the `X-API-Key` header:

```
X-API-Key: your-api-key
```

### Example: create a log entry

```bash
curl -X POST http://localhost:8000/api/v1/audit-logs/ \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "actor_id": "user-123",
    "actor_type": "user",
    "action": "document.delete",
    "status": "success",
    "resource_type": "document",
    "resource_id": "doc-456",
    "service_name": "document-service",
    "trace_id": "trace-abc"
  }'
```

---

## Integrating from Another Service

Add this shared helper to your service:

```python
import httpx

AUDIT_URL = "http://audit-log-service:8000/api/v1/audit-logs/"
API_KEY   = "your-api-key"

async def emit_audit_log(payload: dict) -> None:
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            AUDIT_URL,
            json=payload,
            headers={"X-API-Key": API_KEY},
            timeout=5,
        )
        resp.raise_for_status()
```

---

## Jenkins CI/CD

The `Jenkinsfile` defines:
- Lint (`ruff`) + security scan (`bandit`)
- Unit/integration tests with coverage gate (≥ 80 %)
- Docker build + push on `main` / `release/*`
- Staging auto-deploy, production deploy behind manual approval

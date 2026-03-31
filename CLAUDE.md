# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# Uniforma project rules

This repository contains production-critical code.

Global rules:
- Do not break the site.
- Do not guess.
- Always inspect exact files before changing code.
- Prefer root-cause fixes over frontend workarounds.
- Do not change unrelated files.
- After code changes, always verify with real output.
- For frontend work: never touch backend or ingestion.
- For backend work: never use frontend hacks to hide bad data.
- For pipeline work: treat PIM -> normalization -> backend as the source of truth.

Preferred working style:
1. Explain exact scope.
2. Show files involved.
3. Make smallest safe change.
4. Verify with commands/output.
5. Report what changed and what did not change.

---

## Architecture Overview

Three separate applications share a PostgreSQL database and storage volume:

| App | Dir | Port | Runtime |
|-----|-----|------|---------|
| API (FastAPI) | `app/` | 9100 | Docker / Uvicorn |
| Admin panel | `admin/` | 3001 | PM2 / Next.js 14 |
| Public frontend | `frontend/` | 3000 | PM2 / Next.js 14 |

The `backend/` directory is a legacy structure (old import scripts). The active backend is `app/`.

---

## Backend (`app/`)

### Commands

```bash
# Run API locally (requires .env)
uvicorn app.main:app --reload --port 8000

# Run via Docker (production-like)
docker-compose up -d

# Database migrations
alembic upgrade head
alembic revision --autogenerate -m "description"

# Check API health
curl http://localhost:9100/api/v1/health
```

### Key data flow

```
PIM CSV → PimIngestionService → ProductRepository (upsert) → FtpImageService → Cache invalidation
```

- `app/services/pim_ingestion_service.py` — Parses CSV (delimiter `;`, Swedish text), normalizes sizes/materials/care/sectors, expands variants per size, hashes rows to detect changes
- `app/services/pim_sync_service.py` — Orchestrates sync; uses `pg_try_advisory_lock()` to prevent concurrent runs; triggers image sync; writes to `sync_runs` table
- `app/services/ftp_image_service.py` — Downloads from FTP/SFTP/HTTP, converts to WebP (1600×1600, quality 82), stores under `storage/images/`
- `app/services/product_read_service.py` — Public + admin product queries; 5-minute filter cache; `autocomplete()` for search

### Public visibility requires all three:
```python
is_active == True AND deleted_at IS NULL AND is_sales_blocked == False
```

### Repositories vs Services
- `app/repositories/` — Raw DB queries (SQLAlchemy async). Never call directly from endpoints.
- `app/services/` — Business logic. Endpoints call services only.

### Authentication
- JWT (HS256): 15-min access token, 7-day refresh token
- Login: `POST /api/v1/auth/login` (form data, rate-limited 5/300s per IP)
- Route protection: `Depends(get_current_user)` / `Depends(get_current_superuser)`

### Admin overrides
`admin_overrides` table stores field-level edits (name, description, brand) keyed by `(product_id, field_name)`. These overlay PIM data without modifying source records.

### Scheduled jobs (APScheduler)
- PIM sync: daily at 2 AM UTC (env: `PIM_SYNC_CRON_HOUR/MINUTE`)
- Image sync: 15 seconds after startup

### Migrations
All schema changes go through Alembic. Migration files live in `app/db/migrations/versions/`. Never alter tables directly.

---

## Admin Panel (`admin/`)

```bash
cd admin
npm install
npm run dev      # port 3001
npm run build
```

- API calls centralized in `admin/lib/api/client.ts` and `admin/lib/api/endpoints.ts`
- Auth cookie (`AUTH_COOKIE`) checked by Next.js middleware; redirects to `/admin/login` if missing
- State: React Query for server data, React Hook Form + Zod for forms

---

## Frontend (`frontend/`)

```bash
cd frontend
npm install
npm run dev      # port 3000
npm run build
```

- Server components fetch from `${NEXT_PUBLIC_API_URL}/products` with `revalidate: 60`
- No client-side auth — public read-only storefront
- Styling: Tailwind CSS 3.4

---

## Environment Variables (key ones)

| Variable | Used by | Purpose |
|----------|---------|---------|
| `DATABASE_URL` | API | asyncpg connection string |
| `JWT_SECRET_KEY` | API | Access token signing |
| `JWT_REFRESH_SECRET_KEY` | API | Refresh token signing |
| `PIM_CSV_PATH` | API | Path to PIM export file |
| `FTP_HOST/USER/PASS` | API | Image download source |
| `REDIS_URL` | API | Optional filter cache |
| `NEXT_PUBLIC_API_URL` | Frontend | API base URL |

---

## No test suite
There are no automated tests. Verify changes with real API/DB output after every change.

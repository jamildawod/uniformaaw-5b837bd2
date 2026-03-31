---
name: backend-guard
description: enforce strict backend-only operations in /opt/uniforma/backend. use when working with fastapi, database, api endpoints, services, pm2, docker, or server debugging.
---

# RULES

You are working in:

/opt/uniforma/backend

## ALLOWED
- FastAPI code (app/)
- API endpoints
- Database models
- Debugging backend errors
- Running uvicorn
- Managing PM2 backend process
- Checking ports (ss, lsof)
- Checking logs

## REQUIRED BEHAVIOR

When API fails (e.g. port 9100 not responding):

You MUST:
1. Check if service is running
2. Check ports
3. Restart backend
4. Verify with curl

Example:

curl http://127.0.0.1:9100/api/v1/admin/products

## FORBIDDEN
- Do NOT edit frontend (/opt/uniforma/frontend)
- Do NOT edit admin (/opt/uniforma-admin UI)
- Do NOT touch Next.js UI

## IF TASK REQUIRES FRONTEND

STOP and respond:

"This is a frontend issue. Switch to /opt/uniforma/frontend with frontend-guard."

## IF TASK REQUIRES ADMIN UI

STOP and respond:

"This is an admin UI issue. Switch to /opt/uniforma-admin with admin-guard."

## GOAL

Ensure backend is ALWAYS running and API returns 200.
Fix server issues first before touching anything else.

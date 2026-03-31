---
name: frontend-guard
description: enforce strict boundaries for storefront frontend work in /opt/uniforma/frontend. use when working with next.js ui, pages, components, styling, or frontend data fetching. prevents any backend or admin modifications.
---

# RULES

You are working in:

/opt/uniforma/frontend

## ALLOWED
- Edit Next.js pages (app/)
- Edit components
- Styling (Tailwind, CSS)
- Frontend data fetching
- UI logic

## FORBIDDEN
- Do NOT edit backend (/opt/uniforma/backend)
- Do NOT edit admin (/opt/uniforma-admin)
- Do NOT start or manage backend services
- Do NOT run pm2 for backend
- Do NOT modify API servers

## IF TASK REQUIRES BACKEND

STOP immediately and respond:

"This requires backend changes. Switch to /opt/uniforma/backend with backend-guard."

## IF TASK REQUIRES ADMIN

STOP and respond:

"This requires admin changes. Switch to /opt/uniforma-admin with admin-guard."

## GOAL

Focus ONLY on storefront UI and data display.
Never attempt to fix server issues from here.

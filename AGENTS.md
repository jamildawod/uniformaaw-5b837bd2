# AGENTS.md

## Global rules
- Never make broad changes across frontend and backend in the same pass unless explicitly requested.
- Prefer minimal diffs.
- Verify before and after changes.
- Do not rename public routes, API fields, or DB-facing identifiers unless explicitly requested.
- Never edit files outside the allowed scope for the selected guard.
- If a task crosses boundaries, stop and state which guard should handle it instead.

## Repo structure
- Storefront frontend: /opt/uniforma/frontend
- Storefront backend: /opt/uniforma/app
- Admin backend: /opt/uniforma/app/api/v1/admin and related backend code under /opt/uniforma/app

## Guard selection
- Use storefront-frontend-guard for customer-facing UI, components, layout, styling, frontend routing, filters, menus, product cards, product page presentation, and shop UX in /opt/uniforma/frontend.
- Use storefront-backend-guard for customer-facing API behavior, category filtering, product read services, repositories, sync-safe backend logic, and ingestion-adjacent backend code in /opt/uniforma/app excluding admin endpoints unless explicitly admin-specific.
- Use admin-backend-guard for admin API endpoints, admin auth/backend behavior, admin sync endpoints, admin services, and admin-related repository/service code inside /opt/uniforma/app.

## Hard boundaries
- Storefront frontend must not edit backend files.
- Storefront backend must not edit frontend files.
- Admin backend must not edit storefront frontend or admin frontend files.
- If the request mixes areas, split the work conceptually and handle only the allowed area.

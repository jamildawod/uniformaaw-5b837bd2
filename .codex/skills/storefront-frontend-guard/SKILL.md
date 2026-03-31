---
name: storefront-frontend-guard
description: use when the task is about customer-facing frontend work in the uniforma project, including ui, layout, styling, navigation, mega menus, category presentation, product cards, product detail presentation, search ux, filtering ui, and frontend routing under /opt/uniforma/frontend. prefer staying in storefront frontend scope, but allow small related backend or shared-code adjustments when they are necessary to complete the requested fix safely.
---

# Storefront Frontend Guard

Use this skill for customer-facing frontend work in the Uniforma storefront.

## Default approach

- Prefer staying inside storefront frontend scope.
- Prefer the smallest useful patch that solves the requested task.
- Preserve existing behavior unless the task is specifically to change behavior.
- Preserve existing copy/content unless the user asks to rewrite it.
- Avoid broad cleanup, refactors, renames, or redesigns unless they help complete the task.
- Do not fake backend behavior in the frontend when the real issue is clearly backend-related.
- Allow small related backend, API, or shared-code adjustments when they are necessary to fully solve the task.

## Scope guidance

Typical storefront scope includes:

- `/opt/uniforma/frontend/**`
- storefront components
- storefront routes
- Tailwind and styling
- customer-facing navigation
- product and category presentation
- frontend state/rendering logic
- static assets in `frontend/public`

Small related changes outside this area are allowed when they are directly connected to the requested fix.

## Preferred workflow

### 1. Identify the real issue
Determine whether the problem is visual, interaction-related, rendering/state-related, or actually data-related.

### 2. Keep changes focused
Edit the minimum useful set of files, but do not artificially avoid a necessary adjacent fix.

### 3. Separate frontend and backend reasoning
If a task spans frontend and backend, keep it clear which part is frontend and which part is backend.

### 4. Verify sensibly
Run a relevant check when practical, such as:
- build
- typecheck
- lint for touched files
- quick manual logic review

Use best-effort verification when full validation is too heavy for the task.

## Decision rules

### If the issue is purely visual
Change only storefront UI/layout files.

### If the issue is storefront UX
Change only the page/component logic needed, plus any small related shared logic if necessary.

### If the issue appears data-related
Check whether it is really a frontend rendering/state issue first, but do not block yourself from making a small backend fix if that is clearly the real cause.

### If the issue spans storefront and backend
It is okay to touch both when needed, but keep the changes minimal and directly related to the task.

## Output

Keep reporting concise. A short summary is enough:
- changed files
- what changed
- verification if any

---
name: uniforma-backend-guard
description: use when the task is about backend work in the uniforma project, including api behavior, repositories, services, product filtering, category mapping, auth-related backend behavior, ingestion-adjacent logic, admin backend behavior, and storefront backend behavior under /opt/uniforma/app. prefer backend-first fixes for backend/data issues, but allow small related frontend adjustments when they are necessary to complete the task safely.
---

# Uniforma Backend Guard

Use this skill for backend work in the Uniforma project.

## Default approach

- Prefer backend correctness and data integrity.
- Prefer fixing backend or data problems in the backend instead of masking them in the frontend.
- Prefer the smallest safe patch that solves the requested task.
- Keep changes focused on the relevant area, but allow small adjacent edits when needed to fully resolve the issue.
- Preserve existing API contracts unless the task clearly requires a change.
- Avoid broad cleanup, schema redesigns, renames, or refactors unless they are directly useful for the requested task.

## Scope guidance

Typical backend scope includes:

- `/opt/uniforma/app/**`
- API endpoints
- repositories
- services
- auth-related backend behavior
- product read/write logic
- category filtering and mapping logic
- ingestion-adjacent backend logic
- backend behavior affecting admin or storefront output

Related changes outside backend are allowed when they are small, necessary, and directly tied to the fix.

## Preferred workflow

### 1. Identify the root cause
Trace the issue to the actual backend path before changing code when practical.

### 2. Keep the solution proportional
Make the smallest change that fully solves the task, but do not avoid necessary related edits just because they touch nearby files.

### 3. Separate concerns clearly
If a task spans backend and frontend, keep the backend reasoning clear and avoid mixing unrelated visual changes into the same patch.

### 4. Verify sensibly
Run a relevant check when practical, such as:
- targeted endpoint verification
- targeted tests
- syntax or type checks
- API or DB output inspection

Use best-effort verification when full validation would be unnecessarily heavy.

## Decision rules

### If the issue is data-related
Trace the path through:
- source
- parser or service
- model or repository
- database
- API response

### If storefront output is wrong
Fix it in backend when the root cause is backend or data logic. Small frontend follow-up adjustments are allowed if needed to complete the task cleanly.

### If admin behavior is affected
Prefer a minimal backend fix first. Small admin-side adjustments are allowed when needed to align with the backend fix.

## Output

Keep reporting concise. A short summary is enough:
- changed files
- what changed
- verification if any

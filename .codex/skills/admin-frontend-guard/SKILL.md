---
name: admin-frontend-guard
description: use when the task is about admin frontend work in the uniforma project, including admin ui, admin pages, admin components, layout, navigation, forms, tables, filters, publishing views, media views, or other admin-facing frontend files. prefer staying in admin frontend scope, but allow small related backend, api, or shared-code adjustments when they are necessary to complete the requested fix safely.
---

# Admin Frontend Guard

Use this skill for admin frontend work in the Uniforma project.

## Default approach

- Prefer staying inside admin frontend scope.
- Prefer the smallest useful patch that solves the requested task.
- Preserve existing behavior unless the task is specifically to change behavior.
- Preserve existing copy/content unless the user asks to rewrite it.
- Avoid broad cleanup, refactors, renames, or redesigns unless they help complete the task.
- Avoid unnecessary backend or infrastructure changes, but allow small related changes when they are clearly needed to complete the admin task.
- Prefer isolating changes to admin-specific files when practical, without forcing awkward workarounds.

## Scope guidance

Typical admin scope includes:

- admin frontend pages
- admin components
- admin layout and navigation
- admin-facing forms, tables, filters, publishing/media views
- admin-specific hooks, types, utils, and styling
- shared frontend files when the admin task genuinely depends on them

Small related backend or API changes are allowed when they are directly required for the requested fix.

## Preferred workflow

### 1. Identify the real issue
Determine whether the problem is visual, interaction-related, rendering/state-related, or actually caused by backend/API behavior.

### 2. Keep changes focused
Edit the minimum useful set of files, but allow small adjacent fixes when needed to avoid incomplete solutions.

### 3. Separate admin and backend reasoning
If a task spans admin and backend, keep it clear which changes belong to admin UI and which belong to backend/API logic.

### 4. Verify sensibly
Run a relevant check when practical, such as:
- build
- typecheck
- lint for touched files
- quick manual logic review

Use best-effort verification when full validation is too heavy for the task.

## Decision rules

### If the issue is purely visual
Change only admin UI/layout files.

### If the issue is admin UX
Change only the relevant page/component logic, plus any small related shared logic if needed.

### If the issue appears data-related
Check whether it is a frontend rendering/state issue first, but allow a small backend or API fix if that is clearly the true cause.

### If the issue spans admin and backend
It is okay to touch both when needed, but keep the changes minimal and directly related to the task.

## Output

Keep reporting concise. A short summary is enough:
- changed files
- what changed
- verification if any

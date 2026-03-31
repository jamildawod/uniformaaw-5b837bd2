---
name: admin_guard
description: protect admin frontend work in the uniforma project. use when editing admin ui, admin pages, admin components, layout, navigation, forms, tables, filters, publishing views, media views, or other work under app/admin, components/admin, or admin-facing frontend files. this skill prevents unrelated backend, api, database, auth, ingestion, sync, or infrastructure changes and enforces a minimal-change workflow with verification and a structured report.
---

# Admin Guard

Follow this skill whenever working on the Uniforma admin frontend.

## Core rules

- Do not modify backend, API routes, database models, migrations, ingestion, sync, Docker, nginx, pm2, or infrastructure unless the user explicitly asks for that and the task cannot be completed otherwise.
- Stay inside admin frontend scope only.
- Edit only files directly relevant to the requested task.
- Prefer the smallest safe patch.
- Do not do broad cleanup, refactors, renames, or redesigns unless explicitly requested.
- Preserve existing behavior unless the task is specifically to change behavior.
- Preserve existing copy/content unless the user explicitly asks to rewrite text.
- Avoid touching shared frontend files if the change can be isolated to admin-specific files.
- If a requested change appears to require backend work, state that clearly before making any non-admin changes.

## Allowed scope

Typical allowed paths include:

- `app/admin/**`
- `components/admin/**`
- `components/layout/admin-shell*`
- admin-specific hooks, types, or utils
- admin-specific styling related to the task
- admin-facing frontend files that clearly belong to the admin panel

Be conservative with anything outside those paths.

## Protected scope

Do not touch these unless the user explicitly requests it:

- `app/api/**`
- backend services and repositories
- database schema or migrations
- auth implementation
- sync / ftp / ingestion logic
- infrastructure and deployment config
- public storefront pages unless the admin task directly depends on them

## Required workflow

### 1. Identify relevant files first
Before editing, determine the minimum set of files needed.

### 2. Explain the intended change
State briefly:
- what will change
- which files will be edited
- what will not be touched

### 3. Apply the smallest possible patch
Make only the changes needed to solve the task.

### 4. Verify
Run the smallest relevant validation available, such as:
- build
- typecheck
- lint for touched files if available

If full verification is too heavy, run the closest safe check and say what was verified.

### 5. Report
Always end with a short structured report containing:
- changed files
- what changed
- what was not changed
- verification result

## Decision rules

### If the issue is purely visual
Only change admin UI/layout files.

### If the issue is admin UX
Change only the admin page/component logic needed for the UX fix.

### If the issue appears to be data-related
First verify whether it is actually a frontend rendering/state problem before suggesting backend changes.

### If the issue spans admin and backend
Do not silently change both. Explicitly separate:
- admin/frontend work
- backend work

## Output format

Use this structure in your final report:

- **Changed files**
- **What changed**
- **What was not changed**
- **Verification**

Keep it concise and concrete.

## Uniforma-specific guardrail

For Uniforma admin work, assume the safest default is:

- admin UI only
- no backend edits
- no DB edits
- no API edits
- no sync/ingestion edits
- no unrelated storefront edits

Only expand scope when the user explicitly asks for it or when the task is impossible without it.

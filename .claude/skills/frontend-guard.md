# Frontend Guard

Purpose:
Protect Uniforma frontend from accidental breakage.

Use this skill when:
- changing layout
- changing UI
- changing product page presentation
- adjusting homepage design
- fixing frontend-only bugs

Rules:
- Do not touch backend, API, DB, ingestion, or sync.
- Do not change unrelated pages.
- Do not silently refactor.
- Only edit files required for the task.
- Before coding, list exact files to change.
- After coding, run relevant verification.

Required output:
1. Scope
2. Files changed
3. Verification result
4. What was explicitly not changed

---
description: Safe frontend changes for Uniforma. Use for UI/layout work only. Never touch backend, API, ingestion, or unrelated pages. Always verify scope before edits.
---

You are working on Uniforma frontend.

Rules:
- Do not break existing pages.
- Do not touch backend, API, DB, ingestion, or sync logic.
- Only edit files required for the requested frontend task.
- Keep layout/design scope strict.
- Before changing code, list exact files to touch.
- After changing code, run relevant verification.
- If scope drifts, stop and say what would be affected.

Workflow:
1. Identify exact frontend files involved.
2. Explain what will change and what will not change.
3. Make the smallest safe patch.
4. Run build/typecheck if relevant.
5. Report:
   - files changed
   - what changed
   - what was explicitly not changed

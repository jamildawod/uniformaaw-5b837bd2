---
description: Safe backend work for Uniforma. Use for ingestion, API, DB, and sync logic. Never patch frontend as a workaround for backend data problems.
---

You are working on Uniforma backend.

Rules:
- Treat data correctness as primary.
- Never use frontend hacks to hide backend/data issues.
- For ingestion bugs, trace: source file -> parser -> model -> DB -> API.
- Show exact code paths before patching.
- Prefer minimal, reversible fixes.
- Verify with real DB/API output after changes.

Workflow:
1. Map root cause exactly.
2. Show files/functions involved.
3. Make smallest safe backend fix.
4. Rebuild/restart only if needed.
5. Verify:
   - DB state
   - API output
   - no unrelated changes

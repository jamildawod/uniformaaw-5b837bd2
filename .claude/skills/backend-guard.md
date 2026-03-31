# Backend Guard

Purpose:
Protect Uniforma backend data integrity.

Use this skill when:
- debugging ingestion
- fixing API/data mapping
- working with DB models
- fixing sync logic
- tracing PIM -> DB -> API

Rules:
- Never solve backend data problems with frontend hacks.
- Trace exact path: source -> parser -> model -> DB -> API.
- Show exact code path before patching.
- Prefer minimal safe fixes.
- Verify with DB/API output after changes.

Required output:
1. Root cause
2. Files/functions involved
3. Patch made
4. Verification output
5. What was not changed

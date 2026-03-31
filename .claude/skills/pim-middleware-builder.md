# PIM Middleware Builder

Purpose:
Build and maintain the VPS program between PIM source and Uniforma backend.

Use this skill when:
- designing the middleware service
- parsing PIM/CSV
- splitting semicolon-separated fields
- validating product/variant/image data
- preparing clean structured data before backend ingestion

Rules:
- Keep this separate from frontend concerns.
- Do not silently drop rows or values without reporting them.
- Normalize sizes, colors, EANs, and image references.
- Produce logs and validation summaries.
- Prefer Python/FastAPI-compatible architecture.

Required output:
1. Input format
2. Normalization rules
3. Validation rules
4. Program structure
5. Test commands
6. Sample output

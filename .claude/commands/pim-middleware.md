---
description: Build and maintain Uniforma PIM middleware. Use for the VPS program between PIM source and backend. Normalize, validate, split variants, map images, and produce clean data before backend ingestion.
---

You are designing/building the Uniforma PIM middleware service.

Purpose:
- Sit between PIM source and Uniforma backend.
- Run on VPS.
- Normalize and validate product data before backend receives it.

Responsibilities:
- fetch source file
- parse CSV/PIM safely
- split semicolon-separated fields
- normalize sizes/colors/EAN/images
- validate rows and variants
- produce logs and error reports
- send only clean structured data onward

Rules:
- Do not mix frontend work into this task.
- Do not silently drop data without reporting it.
- If a field is ambiguous, log it explicitly.
- Prefer Python/FastAPI-compatible design for Uniforma.

Workflow:
1. Map source format.
2. Define normalized schema.
3. Define validation rules.
4. Build parser/transformer/validator flow.
5. Show test commands and sample outputs.
6. Report what reaches backend and why.

---
name: Search Autocomplete Architecture
description: Current state of frontend search — uses client-side full-catalog fetch, should migrate to API endpoint
type: project
---

## Current state (as of 2026-03-27)

- `frontend/components/search/SearchAutocomplete.tsx` fetches `GET /products?limit=2000` to build an in-memory catalog
- Filtering is done client-side with a scoring algorithm
- Module-level singleton `searchCatalogPromise` means the 2000-product payload is fetched once per page load
- 300ms debounce IS already implemented (debounceRef + setTimeout)
- `RESULT_LIMIT = 5` is already defined

## The better path (already exists in backend)

- `GET /api/v1/products/autocomplete?q={q}&limit={n}` in `public_products.py`
- Repository `list_autocomplete()` returns ranked lightweight dicts `{label, value, slug, id}`
- Ranking uses CASE expression with scores for exact/prefix/contains matches on external_id, supplier_sku, name
- `AutocompleteItem` schema in `app/schemas/product.py` already has `image_url: str | None = None` field
- `fetchAutocomplete()` helper already exists in `frontend/lib/api.ts`

## Planned migration

Replace `fetchSearchCatalog()` + `searchProducts()` in SearchAutocomplete.tsx with calls to
`fetchAutocomplete(trimmed, 5)`. Add useRef Map cache for in-session deduplication.
Must adjust rendering since AutocompleteItem uses `label`/`value`/`imageUrl` not `product.name`/`getItemNo()`.

## Scaling concern

The 2000-product catalog fetch is a scaling time bomb. Must migrate to API-based autocomplete before catalog grows.

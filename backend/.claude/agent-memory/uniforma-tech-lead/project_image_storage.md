---
name: Image Storage Architecture
description: How product images are stored, served, and URL-resolved in Uniforma — including a latent /media/ 404 bug
type: project
---

## Active image pipeline

- `ImageService.store_image_bytes()` writes to `settings.product_upload_root` = `/opt/uniforma/storage/uploads/products/`
- Filename scheme: `{sha256_16}-{safe_stem}.webp` (NOT `{item_no}.webp`)
- `local_path` stored in DB as `/uploads/products/{filename}`
- FastAPI mounts `/uploads` → `/opt/uniforma/storage/uploads` in `app/main.py`
- Nginx serves `/uploads/` directly from disk with `expires 30d` + `immutable` cache headers
- As of 2026-03-27: ~1,308 images already downloaded and working

## Legacy image path (latent bug)

- Old pipeline wrote files to `settings.image_storage_root` = `/opt/uniforma/storage/images/`
- `product_read_service._resolve_product_image_url()` converts these `local_path` values to `/media/` URLs
- `/media/` is NOT mounted in `app/main.py` and NOT in nginx — those URLs currently 404
- Fix: add `StaticFiles` mount for `/media` in `app/main.py` pointing to `settings.image_storage_root`
- Fix: add `location /media/` block in nginx with same cache headers as `/uploads/`

## Storage directories under /opt/uniforma/storage/

- `images/http/`, `images/CD/`, `images/Generic/`, `images/HEJ/`, `images/MAR/` — old pipeline output
- `uploads/products/` — current pipeline output (active, 1308 files)

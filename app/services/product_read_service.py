import uuid

from app.models.product_image import ProductImage as _ProductImage

# Maps root category slug → the sector slug used in ?sector= product filtering.
# These correspond exactly to _SECTOR_KEYWORDS keys in product_repository.py.
_CATEGORY_SECTOR_MAP: dict[str, str] = {
    "dental": "dental",
    "djursjukvard": "djursjukvard",
    "kok": "kok",
    "skonhet-halsa": "beauty",
    "stad-service": "stad",
    "vard-omsorg": "vard",
}


def _resolve_product_image_url(img: "_ProductImage") -> str | None:
    """Mirror ProductImageRead.url resolution logic for plain ORM instances."""
    lp = img.local_path
    if lp:
        if lp.startswith(("http://", "https://", "/uploads/", "/media/")):
            return lp
        idx = lp.find("/images/")
        if idx != -1:
            return f"/media/{lp[idx + len('/images/'):]}"
        idx2 = lp.find("/uploads/")
        if idx2 != -1:
            return f"/uploads/{lp[idx2 + len('/uploads/'):]}"
    ep = img.external_path
    if ep:
        if ep.startswith(("http://", "https://")):
            return ep
        return f"/media/{ep.lstrip('/')}"
    return None


from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError

from app.core.logging import get_logger
from app.models.admin_override import AdminOverride
from app.models.product import Product
from app.models.product_image import ProductImage
from app.repositories.admin_override_repository import AdminOverrideRepository
from app.repositories.product_repository import ProductRepository
from app.schemas.category import CategoryListItem
from app.schemas.product import (
    AdminImageCreateRequest,
    AdminImageReorderRequest,
    AdminProductRead,
    AdminOverridePatchRequest,
    AdminProductUpdateRequest,
    AdminVariantUpdateRequest,
    AutocompleteItem,
    FiltersRead,
    ProductRead,
    ProductVariantRead,
)
from app.services.cache_service import CacheService

ALLOWED_OVERRIDE_FIELDS = {
    "name",
    "description",
    "brand",
}


class ProductReadService:
    FILTERS_CACHE_KEY = "public:filters:v2"

    def __init__(
        self,
        product_repository: ProductRepository,
        admin_override_repository: AdminOverrideRepository,
        cache_service: CacheService | None = None,
    ) -> None:
        self.product_repository = product_repository
        self.admin_override_repository = admin_override_repository
        self.cache_service = cache_service
        self.logger = get_logger(self.__class__.__name__)

    async def list_public_products(
        self,
        limit: int = 50,
        offset: int = 0,
        category_slug: str | None = None,
        sector_slug: str | None = None,
        color: str | None = None,
        size: str | None = None,
        search: str | None = None,
    ) -> list[ProductRead]:
        products = await self.product_repository.list_active_products(
            limit=limit,
            offset=offset,
            category_slug=category_slug,
            sector_slug=sector_slug,
            color=color,
            size=size,
            search=search,
        )
        override_map = await self.admin_override_repository.list_by_product_ids([product.id for product in products])
        results: list[ProductRead] = []
        for product in products:
            try:
                results.append(self._merge_product(product, override_map.get(product.id, [])))
            except Exception as exc:
                self.logger.warning("Skipped product %s during serialization: %s", product.id, exc)
        return results

    async def list_public_products_by_ids(
        self,
        product_ids: list[str],
    ) -> list[ProductRead]:
        if not product_ids:
            return []

        ordered_ids: list[uuid.UUID] = []
        seen: set[uuid.UUID] = set()
        for product_id in product_ids:
            try:
                parsed_id = uuid.UUID(str(product_id))
            except (TypeError, ValueError, AttributeError):
                continue
            if parsed_id in seen:
                continue
            seen.add(parsed_id)
            ordered_ids.append(parsed_id)

        if not ordered_ids:
            return []

        products = await self.product_repository.list_active_products_by_ids(ordered_ids)
        override_map = await self.admin_override_repository.list_by_product_ids([product.id for product in products])
        merged_products = [
            self._merge_product(product, override_map.get(product.id, []))
            for product in products
        ]
        position = {product_id: index for index, product_id in enumerate(ordered_ids)}
        merged_products.sort(key=lambda product: position.get(product.id, len(position)))
        return merged_products

    async def autocomplete(self, q: str, limit: int = 8) -> list[AutocompleteItem]:
        q = (q or "").strip()
        if not q:
            return []
        try:
            rows = await self.product_repository.list_autocomplete(q=q, limit=limit)
            return [AutocompleteItem.model_validate(row) for row in rows]
        except Exception as exc:
            self.logger.error("autocomplete failed for q=%r: %s", q, exc)
            return []

    async def get_filters(self) -> FiltersRead:
        if self.cache_service is not None:
            try:
                cached = await self.cache_service.get_json(self.FILTERS_CACHE_KEY)
                if cached is not None:
                    return FiltersRead.model_validate(cached)
            except Exception as exc:
                self.logger.warning("Filters cache lookup failed: %s", exc)

        data = await self.product_repository.get_filters()
        payload = FiltersRead.model_validate(data)

        if self.cache_service is not None:
            try:
                await self.cache_service.set_json(
                    self.FILTERS_CACHE_KEY,
                    payload.model_dump(mode="json"),
                    ttl_seconds=self.cache_service.settings.filters_cache_ttl_seconds,
                )
            except Exception as exc:
                self.logger.warning("Filters cache write failed: %s", exc)

        return payload

    async def list_categories(self) -> list[CategoryListItem]:
        categories = await self.product_repository.list_active_categories()

        # Auto-resolve images for categories that have no image set
        null_ids = [c.id for c in categories if not getattr(c, "image", None)]
        auto_images: dict[int, str] = {}
        if null_ids:
            img_map = await self.product_repository.get_primary_images_for_categories(null_ids)
            for cat_id, img in img_map.items():
                url = _resolve_product_image_url(img)
                if url:
                    auto_images[cat_id] = url

        return [
            CategoryListItem.model_validate(
                {
                    "id": category.id,
                    "name": category.name,
                    "slug": category.slug,
                    "image": getattr(category, "image", None) or auto_images.get(category.id),
                    "parent_id": category.parent_id,
                }
            )
            for category in categories
        ]

    async def list_sector_categories(self) -> list[CategoryListItem]:
        categories = await self.product_repository.list_sector_categories()
        null_ids = [c.id for c in categories if not getattr(c, "image", None)]
        auto_images: dict[int, str] = {}
        if null_ids:
            img_map = await self.product_repository.get_primary_images_for_categories(null_ids)
            for cat_id, img in img_map.items():
                url = _resolve_product_image_url(img)
                if url:
                    auto_images[cat_id] = url
        return [
            CategoryListItem.model_validate(
                {
                    "id": category.id,
                    "name": category.name,
                    "slug": category.slug,
                    "image": getattr(category, "image", None) or auto_images.get(category.id),
                    "parent_id": category.parent_id,
                }
            )
            for category in categories
        ]

    async def list_root_categories(self) -> list[CategoryListItem]:
        categories = await self.product_repository.list_root_categories()
        null_ids = [c.id for c in categories if not getattr(c, "image", None)]
        auto_images: dict[int, str] = {}
        if null_ids:
            img_map = await self.product_repository.get_primary_images_for_categories(null_ids)
            for cat_id, img in img_map.items():
                url = _resolve_product_image_url(img)
                if url:
                    auto_images[cat_id] = url
        return [
            CategoryListItem.model_validate(
                {
                    "id": category.id,
                    "name": category.name,
                    "slug": category.slug,
                    "image": getattr(category, "image", None) or auto_images.get(category.id),
                    "parent_id": category.parent_id,
                    "sector_slug": _CATEGORY_SECTOR_MAP.get(category.slug),
                }
            )
            for category in categories
        ]

    async def get_public_product(self, slug: str) -> ProductRead | None:
        product = await self.product_repository.get_product_by_slug(slug)
        if product is None:
            return None
        overrides = await self.admin_override_repository.list_by_product_ids([product.id])
        return self._merge_product(product, overrides.get(product.id, []))

    async def get_public_variants(self, slug: str) -> list[ProductVariantRead] | None:
        product = await self.product_repository.get_product_by_slug(slug)
        if product is None:
            return None
        return [ProductVariantRead.model_validate(variant) for variant in product.variants if variant.is_active]

    async def list_admin_products(
        self,
        limit: int = 50,
        offset: int = 0,
        search: str | None = None,
        category_id: int | None = None,
        is_active: bool | None = None,
        has_override: bool | None = None,
    ) -> list[AdminProductRead]:
        products = await self.product_repository.list_products(
            limit=limit,
            offset=offset,
            search=search,
            category_id=category_id,
            is_active=is_active,
            has_override=has_override,
        )
        override_map = await self.admin_override_repository.list_by_product_ids([product.id for product in products])
        return [self._merge_admin_product(product, override_map.get(product.id, [])) for product in products]

    async def get_admin_product(self, product_id: uuid.UUID) -> AdminProductRead | None:
        product = await self.product_repository.get_product_by_id(product_id)
        if product is None:
            return None
        override_map = await self.admin_override_repository.list_by_product_ids([product.id])
        return self._merge_admin_product(product, override_map.get(product.id, []))

    async def patch_admin_product(
        self,
        product_id: uuid.UUID,
        payload: AdminOverridePatchRequest,
        updated_by: str,
    ) -> AdminProductRead | None:
        product = await self.product_repository.get_product_by_id(product_id)
        if product is None:
            return None

        for field_name, override_value in payload.overrides.items():
            if field_name not in ALLOWED_OVERRIDE_FIELDS:
                self.logger.warning(
                    "Rejected disallowed override field '%s' for product %s",
                    field_name,
                    product_id,
                )
                continue
            override = await self.admin_override_repository.get_by_product_and_field(product_id, field_name)
            if override is None:
                override = AdminOverride(
                    product_id=product_id,
                    field_name=field_name,
                    override_value=override_value,
                    updated_by=updated_by,
                )
                await self.admin_override_repository.add(override)
            else:
                override.override_value = override_value
                override.updated_by = updated_by

        override_map = await self.admin_override_repository.list_by_product_ids([product.id])
        return self._merge_admin_product(product, override_map.get(product.id, []))

    async def update_admin_product(
        self,
        product_id: uuid.UUID,
        payload: AdminProductUpdateRequest,
    ) -> AdminProductRead | None:
        product = await self.product_repository.get_product_by_id(product_id)
        if product is None:
            return None

        if payload.category_id is not None:
            category = await self.product_repository.get_category_by_id(payload.category_id)
            if category is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Category not found.",
                )

        product.name = payload.name
        product.description = payload.description
        product.category_id = payload.category_id
        product.is_active = payload.is_active

        await self.admin_override_repository.delete_by_product_and_fields(
            product_id,
            ["name", "description"],
        )
        self._apply_product_price(product, payload.price)
        await self.product_repository.flush()
        return await self._refresh_admin_product(product_id)

    async def update_admin_variant(
        self,
        product_id: uuid.UUID,
        variant_id: int,
        payload: AdminVariantUpdateRequest,
    ) -> AdminProductRead | None:
        product = await self.product_repository.get_product_by_id(product_id)
        if product is None:
            return None

        variant = self._get_variant_for_product(product, variant_id)
        if variant is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Variant not found.",
            )

        variant.sku = payload.sku
        variant.ean = payload.ean
        variant.color = payload.color
        variant.size = payload.size
        variant.price = payload.price
        if "currency" in payload.model_fields_set:
            variant.currency = payload.currency
        variant.stock_quantity = payload.stock_quantity
        variant.is_active = payload.is_active

        try:
            await self.product_repository.flush()
        except IntegrityError as exc:
            session = self.product_repository.session
            await session.rollback()
            self.logger.warning(
                "Rejected variant update for product %s variant %s",
                product_id,
                variant_id,
                extra={
                    "event": "admin_product_variant_integrity_error",
                    "product_id": str(product_id),
                    "variant_id": variant_id,
                    "sku": payload.sku,
                    "error": str(exc),
                },
            )
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Variant update violates a uniqueness constraint.",
            ) from exc

        return await self._refresh_admin_product(product_id)

    async def delete_admin_variant(
        self,
        product_id: uuid.UUID,
        variant_id: int,
    ) -> AdminProductRead | None:
        product = await self.product_repository.get_product_by_id(product_id)
        if product is None:
            return None

        variant = self._get_variant_for_product(product, variant_id)
        if variant is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Variant not found.",
            )

        await self.product_repository.delete_variant(variant)
        return await self._refresh_admin_product(product_id)

    async def add_product_image(
        self,
        product_id: uuid.UUID,
        payload: AdminImageCreateRequest,
    ) -> AdminProductRead | None:
        product = await self.product_repository.get_product_by_id(product_id)
        if product is None:
            return None

        image = ProductImage(
            product_id=product_id,
            variant_id=payload.variant_id,
            external_path=payload.external_path,
            local_path=payload.local_path,
            is_primary=payload.is_primary,
            sort_order=payload.sort_order,
        )
        try:
            await self.product_repository.add_image(image)
        except IntegrityError as exc:
            session = self.product_repository.session
            await session.rollback()
            self.logger.warning(
                "Rejected duplicate product image for external_path '%s'",
                payload.external_path,
                extra={
                    "event": "admin_product_image_integrity_error",
                    "product_id": str(product_id),
                    "external_path": payload.external_path,
                    "error": str(exc),
                },
            )
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Image with this external_path already exists.",
            ) from exc
        refreshed = await self.product_repository.get_product_by_id(product_id)
        override_map = await self.admin_override_repository.list_by_product_ids([product_id])
        return self._merge_admin_product(refreshed, override_map.get(product_id, []))

    async def set_primary_product_image(
        self,
        product_id: uuid.UUID,
        image_id: int,
    ) -> AdminProductRead | None:
        product = await self.product_repository.get_product_by_id(product_id)
        if product is None:
            return None

        image = self._get_image_for_product(product, image_id)
        if image is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Image not found.",
            )

        for candidate in product.images:
            candidate.is_primary = candidate.id == image_id

        await self.product_repository.flush()
        return await self._refresh_admin_product(product_id)

    async def delete_product_image(
        self,
        product_id: uuid.UUID,
        image_id: int,
    ) -> AdminProductRead | None:
        product = await self.product_repository.get_product_by_id(product_id)
        if product is None:
            return None

        image = self._get_image_for_product(product, image_id)
        if image is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Image not found.",
            )

        was_primary = image.is_primary
        remaining_images = [candidate for candidate in product.images if candidate.id != image_id]
        await self.product_repository.delete_image(image)

        if remaining_images and (was_primary or not any(candidate.is_primary for candidate in remaining_images)):
            for candidate in remaining_images:
                candidate.is_primary = False
            min(remaining_images, key=lambda candidate: (candidate.sort_order, candidate.id)).is_primary = True

        await self.product_repository.flush()
        return await self._refresh_admin_product(product_id)

    async def reorder_product_images(
        self,
        product_id: uuid.UUID,
        payload: AdminImageReorderRequest,
    ) -> AdminProductRead | None:
        product = await self.product_repository.get_product_by_id(product_id)
        if product is None:
            return None

        if len(payload.image_ids) != len(set(payload.image_ids)):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="image_ids must not contain duplicates.",
            )

        product_image_ids = [image.id for image in product.images]
        if set(payload.image_ids) != set(product_image_ids):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="image_ids must match the product's images exactly.",
            )

        image_map = {image.id: image for image in product.images}
        for sort_order, image_id in enumerate(payload.image_ids):
            image_map[image_id].sort_order = sort_order

        if product.images and not any(image.is_primary for image in product.images):
            image_map[payload.image_ids[0]].is_primary = True

        await self.product_repository.flush()
        return await self._refresh_admin_product(product_id)

    def _merge_product(self, product: Product, overrides: list[AdminOverride]) -> ProductRead:
        merged = ProductRead.model_validate(product).model_dump()
        applied_overrides = self._filter_overrides(overrides)
        for field_name, override_value in applied_overrides.items():
            if field_name in merged:
                merged[field_name] = override_value
        return ProductRead.model_validate(merged)

    def _merge_admin_product(self, product: Product, overrides: list[AdminOverride]) -> AdminProductRead:
        merged = self._merge_product(product, overrides).model_dump()
        merged["applied_overrides"] = self._filter_overrides(overrides)
        merged["sectors"] = [sector.name for sector in (product.sectors or [])]
        return AdminProductRead.model_validate(merged)

    def _filter_overrides(
        self,
        overrides: list[AdminOverride],
    ) -> dict[str, str | int | float | bool | list | dict | None]:
        filtered: dict[str, str | int | float | bool | list | dict | None] = {}
        for override in overrides:
            if override.field_name not in ALLOWED_OVERRIDE_FIELDS:
                self.logger.warning(
                    "Ignored disallowed override field '%s' for product %s",
                    override.field_name,
                    override.product_id,
                )
                continue
            filtered[override.field_name] = override.override_value
        return filtered

    def _apply_product_price(self, product: Product, price) -> None:
        variants = [variant for variant in product.variants if variant.deleted_at is None]
        if not variants:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Product price is derived from variants. Add or update a variant instead.",
            )

        distinct_prices = {variant.price for variant in variants}
        if len(variants) > 1 and len(distinct_prices) > 1:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Product has multiple variant prices. Update variants individually.",
            )

        for variant in variants:
            variant.price = price

    def _get_variant_for_product(self, product: Product, variant_id: int):
        for variant in product.variants:
            if variant.id == variant_id:
                return variant
        return None

    def _get_image_for_product(self, product: Product, image_id: int):
        for image in product.images:
            if image.id == image_id:
                return image
        return None

    async def _refresh_admin_product(self, product_id: uuid.UUID) -> AdminProductRead:
        refreshed = await self.product_repository.get_product_by_id(product_id)
        if refreshed is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found.",
            )

        override_map = await self.admin_override_repository.list_by_product_ids([product_id])
        return self._merge_admin_product(refreshed, override_map.get(product_id, []))

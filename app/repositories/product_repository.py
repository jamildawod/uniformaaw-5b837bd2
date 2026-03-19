import uuid
from datetime import datetime

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased, selectinload

from app.core.size import ALLOWED_SIZES, normalize_size
from app.models.category import Category
from app.models.product import Product
from app.models.product_image import ProductImage
from app.models.product_variant import ProductVariant
from app.models.supplier import Supplier


class ProductRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_products(self, limit: int = 50, offset: int = 0) -> list[Product]:
        statement = (
            select(Product)
            .where(Product.deleted_at.is_(None))
            .options(
                selectinload(Product.category),
                selectinload(Product.images),
                selectinload(Product.variants).selectinload(ProductVariant.images),
            )
            .order_by(Product.name.asc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(statement)
        return list(result.scalars().unique().all())

    async def list_active_products(
        self,
        limit: int = 50,
        offset: int = 0,
        category_slug: str | None = None,
        color: str | None = None,
        size: str | None = None,
    ) -> list[Product]:
        # Build a subquery to get matching product IDs with filters applied.
        # Select both id and name so ORDER BY name is valid with DISTINCT.
        id_q = select(Product.id, Product.name).where(
            Product.is_active.is_(True),
            Product.deleted_at.is_(None),
        )
        if category_slug:
            id_q = id_q.join(Category, Product.category_id == Category.id).where(
                Category.slug == category_slug
            )
        if color or size:
            id_q = id_q.join(
                ProductVariant, ProductVariant.product_id == Product.id
            ).where(
                ProductVariant.is_active.is_(True),
                ProductVariant.deleted_at.is_(None),
            )
            if color:
                id_q = id_q.where(
                    func.lower(ProductVariant.color) == color.lower()
                )
            if size:
                id_q = id_q.where(
                    func.lower(ProductVariant.size) == size.lower()
                )
        id_subq = (
            id_q.distinct()
            .order_by(Product.name.asc())
            .limit(limit)
            .offset(offset)
            .subquery()
        )

        statement = (
            select(Product)
            .where(Product.id.in_(select(id_subq.c.id)))
            .options(
                selectinload(Product.category),
                selectinload(Product.images),
                selectinload(Product.variants).selectinload(ProductVariant.images),
            )
            .order_by(Product.name.asc())
        )
        result = await self.session.execute(statement)
        return list(result.scalars().unique().all())

    async def get_product_by_slug(self, slug: str) -> Product | None:
        statement = (
            select(Product)
            .where(Product.slug == slug, Product.is_active.is_(True), Product.deleted_at.is_(None))
            .options(
                selectinload(Product.category),
                selectinload(Product.images),
                selectinload(Product.variants).selectinload(ProductVariant.images),
            )
        )
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def get_product_by_id(self, product_id: uuid.UUID) -> Product | None:
        statement = (
            select(Product)
            .where(Product.id == product_id)
            .options(
                selectinload(Product.category),
                selectinload(Product.images),
                selectinload(Product.variants).selectinload(ProductVariant.images),
            )
        )
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def get_by_external_ids(self, external_ids: list[str]) -> dict[str, Product]:
        if not external_ids:
            return {}
        statement = select(Product).where(Product.external_id.in_(external_ids))
        result = await self.session.execute(statement)
        products = result.scalars().all()
        return {product.external_id: product for product in products}

    async def get_by_skus(self, skus: list[str]) -> dict[str, ProductVariant]:
        if not skus:
            return {}
        statement = select(ProductVariant).where(ProductVariant.sku.in_(skus))
        result = await self.session.execute(statement)
        variants = result.scalars().all()
        return {variant.sku: variant for variant in variants}

    async def get_categories_by_slugs(self, slugs: list[str]) -> dict[str, Category]:
        if not slugs:
            return {}
        statement = select(Category).where(Category.slug.in_(slugs))
        result = await self.session.execute(statement)
        categories = result.scalars().all()
        return {category.slug: category for category in categories}

    async def list_active_categories(self) -> list[Category]:
        statement = (
            select(Category)
            .join(Product, Product.category_id == Category.id)
            .where(
                Product.is_active.is_(True),
                Product.deleted_at.is_(None),
            )
            .distinct()
            .order_by(Category.name.asc())
        )
        result = await self.session.execute(statement)
        return list(result.scalars().unique().all())

    async def get_primary_images_for_categories(
        self, category_ids: list[int]
    ) -> dict[int, ProductImage]:
        """Return one image per category (primary-preferred) keyed by category_id.

        Uses PostgreSQL DISTINCT ON to efficiently fetch a single image row per
        category without a Python-side loop.
        """
        if not category_ids:
            return {}
        statement = (
            select(Product.category_id, ProductImage)
            .join(ProductImage, ProductImage.product_id == Product.id)
            .where(
                Product.category_id.in_(category_ids),
                Product.is_active.is_(True),
                Product.deleted_at.is_(None),
            )
            .order_by(
                Product.category_id,
                ProductImage.is_primary.desc(),
                ProductImage.sort_order.asc(),
            )
            .distinct(Product.category_id)
        )
        result = await self.session.execute(statement)
        rows = result.all()
        return {row[0]: row[1] for row in rows}

    async def list_root_categories(self) -> list[Category]:
        """Return categories with parent_id IS NULL that have child categories."""
        ChildCategory = aliased(Category)
        statement = (
            select(Category)
            .join(ChildCategory, ChildCategory.parent_id == Category.id)
            .where(Category.parent_id.is_(None))
            .distinct()
            .order_by(Category.name.asc())
        )
        result = await self.session.execute(statement)
        return list(result.scalars().unique().all())

    async def get_supplier_by_code(self, code: str) -> Supplier | None:
        statement = select(Supplier).where(Supplier.code == code)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def get_images_by_external_paths(self, external_paths: list[str]) -> dict[str, ProductImage]:
        if not external_paths:
            return {}
        statement = select(ProductImage).where(ProductImage.external_path.in_(external_paths))
        result = await self.session.execute(statement)
        images = result.scalars().all()
        return {image.external_path: image for image in images}

    async def list_images_needing_sync(self) -> list[ProductImage]:
        """Return FTP images (non-HTTP) that have no local copy yet."""
        statement = select(ProductImage).where(
            ProductImage.external_path.is_not(None),
            ProductImage.local_path.is_(None),
            ~ProductImage.external_path.startswith("http://"),
            ~ProductImage.external_path.startswith("https://"),
        )
        result = await self.session.execute(statement)
        return list(result.scalars().all())

    async def list_http_images_needing_download(self) -> list[ProductImage]:
        """Return HTTP/HTTPS images that have not been downloaded to local storage yet."""
        statement = select(ProductImage).where(
            ProductImage.external_path.is_not(None),
            ProductImage.local_path.is_(None),
            ProductImage.external_path.startswith("http"),
        )
        result = await self.session.execute(statement)
        return list(result.scalars().all())

    async def get_filters(self) -> dict:
        colors_q = (
            select(func.lower(ProductVariant.color).label("color"))
            .join(Product, ProductVariant.product_id == Product.id)
            .where(
                Product.is_active.is_(True),
                Product.deleted_at.is_(None),
                ProductVariant.is_active.is_(True),
                ProductVariant.deleted_at.is_(None),
                ProductVariant.color.is_not(None),
                ProductVariant.color != "",
            )
            .distinct()
            .order_by("color")
        )
        sizes_q = (
            select(ProductVariant.size.label("size"))
            .join(Product, ProductVariant.product_id == Product.id)
            .where(
                Product.is_active.is_(True),
                Product.deleted_at.is_(None),
                ProductVariant.is_active.is_(True),
                ProductVariant.deleted_at.is_(None),
                ProductVariant.size.is_not(None),
                ProductVariant.size != "",
            )
            .distinct()
        )
        product_count_sq = (
            select(
                Product.category_id.label("category_id"),
                func.count(Product.id).label("cnt"),
            )
            .where(
                Product.is_active.is_(True),
                Product.deleted_at.is_(None),
            )
            .group_by(Product.category_id)
            .subquery()
        )
        categories_q = (
            select(Category)
            .join(product_count_sq, product_count_sq.c.category_id == Category.id)
            .where(product_count_sq.c.cnt >= 3)
            .order_by(product_count_sq.c.cnt.desc())
        )
        colors_result = await self.session.execute(colors_q)
        sizes_result = await self.session.execute(sizes_q)
        categories_result = await self.session.execute(categories_q)
        normalized_sizes = []
        seen_sizes: set[str] = set()
        for row in sizes_result:
            normalized = normalize_size(row.size)
            if normalized is None or normalized in seen_sizes:
                continue
            seen_sizes.add(normalized)
            normalized_sizes.append(normalized)

        normalized_sizes.sort(key=lambda size: ALLOWED_SIZES.index(size))

        return {
            "colors": [r.color for r in colors_result],
            "sizes": normalized_sizes,
            "categories": list(categories_result.scalars().unique().all()),
        }

    async def soft_delete_missing_products(self, seen_at: datetime, deleted_at: datetime) -> None:
        statement = (
            update(Product)
            .where(
                (Product.last_seen_at.is_(None)) | (Product.last_seen_at < seen_at),
                Product.deleted_at.is_(None),
            )
            .values(
                deleted_at=deleted_at,
                is_active=False,
            )
        )
        await self.session.execute(statement)

    async def soft_delete_missing_variants(self, seen_at: datetime, deleted_at: datetime) -> None:
        statement = (
            update(ProductVariant)
            .where(
                (ProductVariant.last_seen_at.is_(None)) | (ProductVariant.last_seen_at < seen_at),
                ProductVariant.deleted_at.is_(None),
            )
            .values(
                deleted_at=deleted_at,
                is_active=False,
            )
        )
        await self.session.execute(statement)

    async def add_category(self, category: Category) -> Category:
        self.session.add(category)
        await self.session.flush()
        return category

    async def add_supplier(self, supplier: Supplier) -> Supplier:
        self.session.add(supplier)
        await self.session.flush()
        return supplier

    async def add_product(self, product: Product) -> Product:
        self.session.add(product)
        await self.session.flush()
        return product

    async def add_variant(self, variant: ProductVariant) -> ProductVariant:
        self.session.add(variant)
        await self.session.flush()
        return variant

    async def add_image(self, image: ProductImage) -> ProductImage:
        self.session.add(image)
        await self.session.flush()
        return image

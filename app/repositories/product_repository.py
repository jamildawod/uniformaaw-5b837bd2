import logging
import uuid
from datetime import datetime

from sqlalchemy import case, func, or_, select, update

logger = logging.getLogger(__name__)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased, selectinload

from app.core.size import ALLOWED_SIZES, normalize_size
from app.models.admin_override import AdminOverride
from app.models.category import Category
from app.models.product import Product
from app.models.product_image import ProductImage
from app.models.product_sector import ProductSector
from app.models.product_variant import ProductVariant
from app.models.supplier import Supplier


class ProductRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    @staticmethod
    def _public_visibility_filters() -> tuple:
        return (
            Product.is_active.is_(True),
            Product.deleted_at.is_(None),
            Product.is_sales_blocked.is_(False),
            func.lower(func.coalesce(Product.lifecycle_status, "")) == "active",
        )

    async def list_products(
        self,
        limit: int = 50,
        offset: int = 0,
        search: str | None = None,
        category_id: int | None = None,
        is_active: bool | None = None,
        has_override: bool | None = None,
    ) -> list[Product]:
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
        if search:
            token = search.lower()
            sku_exists = (
                select(ProductVariant.id)
                .where(
                    ProductVariant.product_id == Product.id,
                    ProductVariant.deleted_at.is_(None),
                    or_(
                        func.lower(ProductVariant.sku).contains(token),
                        func.lower(ProductVariant.supplier_sku).contains(token),
                    ),
                )
                .exists()
            )
            statement = statement.where(
                or_(
                    func.lower(Product.name).contains(token),
                    func.lower(Product.brand).contains(token),
                    sku_exists,
                )
            )
        if category_id is not None:
            statement = statement.where(Product.category_id == category_id)
        if is_active is not None:
            statement = statement.where(Product.is_active.is_(is_active))
        if has_override is True:
            override_exists = (
                select(AdminOverride.id)
                .where(AdminOverride.product_id == Product.id)
                .exists()
            )
            statement = statement.where(override_exists)
        elif has_override is False:
            override_exists = (
                select(AdminOverride.id)
                .where(AdminOverride.product_id == Product.id)
                .exists()
            )
            statement = statement.where(~override_exists)
        result = await self.session.execute(statement)
        return list(result.scalars().unique().all())

    async def list_active_products(
        self,
        limit: int = 50,
        offset: int = 0,
        category_slug: str | None = None,
        sector_slug: str | None = None,
        color: str | None = None,
        size: str | None = None,
        search: str | None = None,
    ) -> list[Product]:
        # Build a subquery to get matching product IDs with filters applied.
        # Select created_at too so default storefront ordering can follow API order
        # instead of alphabetic name sorting.
        #
        # Public visibility rule (applied centrally here, not in ingestion):
        #   - is_active = true
        #   - deleted_at IS NULL
        #   - is_sales_blocked = false   ← sourced from IsSalesBlocked in PIM CSV
        #
        # is_sales_blocked is the primary visibility signal from the PIM source.
        # Ingestion stores all rows broadly; this filter narrows the public view.
        id_q = select(Product.id, Product.name, Product.created_at).where(
            *self._public_visibility_filters(),
        )
        if search:
            # Split into tokens so "mio 102001" requires each token to match somewhere.
            # Within each token: match external_id (ItemNo), name, brand, or SKU.
            for token in search.lower().split():
                token_clean = token.replace("-", "")
                sku_exists = (
                    select(ProductVariant.id)
                    .where(
                        ProductVariant.product_id == Product.id,
                        ProductVariant.deleted_at.is_(None),
                        or_(
                            func.lower(ProductVariant.sku).contains(token),
                            func.replace(func.lower(ProductVariant.sku), "-", "").contains(token_clean),
                            func.lower(ProductVariant.supplier_sku).contains(token),
                            func.replace(func.lower(ProductVariant.supplier_sku), "-", "").contains(token_clean),
                        ),
                    )
                    .exists()
                )
                id_q = id_q.where(
                    or_(
                        # ItemNo (external_id) — exact uses B-tree index
                        func.lower(Product.external_id) == token,
                        Product.external_id.ilike(token + "%"),
                        func.lower(Product.name).contains(token),
                        func.lower(Product.brand).contains(token),
                        sku_exists,
                    )
                )
        if category_slug:
            id_q = id_q.join(Category, Product.category_id == Category.id).where(
                Category.slug == category_slug
            )
        if sector_slug:
            # Map frontend slugs to PIM industry name keywords (case-insensitive ILIKE).
            # PIM stores values like "Restaurang/Café", "Spa & Beauty", "Facility Management"
            # which slugify to "restaurang-cafe", "spa-beauty", "facility-management".
            # Exact slug match fails; keyword match on Category.name is reliable.
            _SECTOR_KEYWORDS: dict[str, list[str]] = {
                "dental": ["dental"],
                "djursjukvard": ["djursjukvård", "djursjukvard"],
                "beauty": ["spa", "beauty", "wellness"],
                "vard": ["vård", "vard", "hemtjänst", "hemtjanst", "fysioterapi", "apotek"],
                "stad": ["städ", "stad", "facility", "service", "lokalvård", "lokalvard"],
                "kok": ["restaurang", "kök", "kok", "café", "cafe", "food", "hotell"],
            }
            keywords = _SECTOR_KEYWORDS.get(sector_slug, [sector_slug])
            SectorCategory = aliased(Category)
            name_conditions = [
                func.lower(SectorCategory.name).contains(kw.lower())
                for kw in keywords
            ]
            id_q = (
                id_q.join(ProductSector, ProductSector.product_id == Product.id)
                .join(SectorCategory, SectorCategory.id == ProductSector.sector_id)
                .where(or_(*name_conditions))
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
        # Rank-aware ordering when a search term is present.
        # Uses a correlated scalar subquery (MAX of CASE) — no extra joins, no N+1.
        # rank_col is added to id_subq SELECT so the outer JOIN can preserve order.
        rank_col = None
        if search:
            search_lower = search.lower().strip()
            search_clean = search_lower.replace("-", "")
            variant_rank_sq = (
                select(
                    func.max(
                        case(
                            (func.lower(ProductVariant.supplier_sku) == search_lower, 100),
                            (func.replace(func.lower(ProductVariant.supplier_sku), "-", "") == search_clean, 90),
                            (func.lower(ProductVariant.supplier_sku).like(search_lower + "%"), 80),
                            (func.replace(func.lower(ProductVariant.supplier_sku), "-", "").like(search_clean + "%"), 70),
                            (func.lower(ProductVariant.sku) == search_lower, 85),
                            (func.lower(ProductVariant.supplier_sku).like("%" + search_lower + "%"), 60),
                            else_=0,
                        )
                    )
                )
                .where(
                    ProductVariant.product_id == Product.id,
                    ProductVariant.deleted_at.is_(None),
                )
                .correlate(Product)
                .scalar_subquery()
            )
            name_rank = case(
                (func.lower(Product.name) == search_lower, 50),
                (func.lower(Product.name).like(search_lower + "%"), 40),
                (func.lower(Product.name).like("%" + search_lower + "%"), 30),
                (func.lower(Product.brand).like(search_lower + "%"), 20),
                (func.lower(Product.brand).like("%" + search_lower + "%"), 10),
                else_=0,
            )
            rank_col = (func.coalesce(variant_rank_sq, 0) + name_rank).label("rank")
            id_q = id_q.add_columns(rank_col)

        if rank_col is not None:
            id_subq = (
                id_q.distinct()
                .order_by(rank_col.desc(), Product.name.asc())
                .limit(limit)
                .offset(offset)
                .subquery()
            )
            statement = (
                select(Product)
                .join(id_subq, Product.id == id_subq.c.id)
                .options(
                    selectinload(Product.category),
                    selectinload(Product.images),
                    selectinload(Product.variants).selectinload(ProductVariant.images),
                )
                .order_by(id_subq.c.rank.desc(), Product.name.asc())
            )
        else:
            id_subq = (
                id_q.distinct()
                .order_by(Product.created_at.desc(), Product.id.desc())
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
                .order_by(Product.created_at.desc(), Product.id.desc())
            )
        result = await self.session.execute(statement)
        return list(result.scalars().unique().all())

    async def list_active_products_by_ids(
        self,
        product_ids: list[uuid.UUID],
    ) -> list[Product]:
        if not product_ids:
            return []

        statement = (
            select(Product)
            .where(
                Product.id.in_(product_ids),
                *self._public_visibility_filters(),
            )
            .options(
                selectinload(Product.category),
                selectinload(Product.images),
                selectinload(Product.variants).selectinload(ProductVariant.images),
            )
        )
        result = await self.session.execute(statement)
        return list(result.scalars().unique().all())

    async def list_autocomplete(self, q: str, limit: int = 8) -> list[dict]:
        """Return lightweight autocomplete suggestions ranked by match quality.

        One row per product (GROUP BY product), ranked by the best variant match.
        Searches external_id (ItemNo), supplier_sku (variant SKU), and name.
        No selectinload — returns raw dicts for low latency.
        """
        if not q or len(q.strip()) < 2:
            return []
        q_lower = q.lower().strip()
        q_clean = q_lower.replace("-", "")

        # external_id is the product-level ItemNo (B-tree index, unique).
        # Exact match uses the index; prefix ILIKE is fast on short result sets.
        # These conditions are evaluated first so article-number lookups are instant.
        rank_expr = func.max(
            case(
                # ItemNo / external_id — highest priority
                (func.lower(Product.external_id) == q_lower, 110),
                (Product.external_id.ilike(q_lower + "%"), 95),
                # supplier_sku (variant-level) — exact and prefix use the B-tree index
                (func.lower(ProductVariant.supplier_sku) == q_lower, 100),
                (func.replace(func.lower(ProductVariant.supplier_sku), "-", "") == q_clean, 90),
                (func.lower(ProductVariant.supplier_sku).like(q_lower + "%"), 80),
                (func.replace(func.lower(ProductVariant.supplier_sku), "-", "").like(q_clean + "%"), 70),
                (func.lower(ProductVariant.sku) == q_lower, 85),
                (func.lower(ProductVariant.supplier_sku).like("%" + q_lower + "%"), 60),
                # Name
                (func.lower(Product.name).like(q_lower + "%"), 40),
                (func.lower(Product.name).like("%" + q_lower + "%"), 30),
                else_=0,
            )
        ).label("rank")

        statement = (
            select(
                Product.id,
                Product.name,
                Product.slug,
                Product.external_id.label("article_number"),
                rank_expr,
            )
            .join(ProductVariant, ProductVariant.product_id == Product.id)
            .where(
                *self._public_visibility_filters(),
                ProductVariant.deleted_at.is_(None),
                or_(
                    # ItemNo exact / prefix — fast paths (indexed)
                    func.lower(Product.external_id) == q_lower,
                    Product.external_id.ilike(q_lower + "%"),
                    # Variant SKU fuzzy — kept as fallback
                    func.lower(ProductVariant.supplier_sku).like("%" + q_lower + "%"),
                    func.replace(func.lower(ProductVariant.supplier_sku), "-", "").like("%" + q_clean + "%"),
                    # Name / brand fuzzy
                    func.lower(Product.name).like("%" + q_lower + "%"),
                    func.lower(Product.brand).like("%" + q_lower + "%"),
                ),
            )
            .group_by(Product.id, Product.name, Product.slug, Product.external_id)
            .order_by(rank_expr.desc(), Product.name.asc())
            .limit(limit)
        )
        try:
            result = await self.session.execute(statement)
            rows = result.all()
        except Exception as exc:
            logger.error("list_autocomplete failed for q=%r: %s", q, exc)
            return []
        return [
            {
                "label": row.name,
                "value": row.article_number or "",
                "slug": row.slug,
                "id": str(row.id),
            }
            for row in rows
        ]

    async def get_product_by_slug(self, slug: str) -> Product | None:
        statement = (
            select(Product)
            .where(Product.slug == slug, *self._public_visibility_filters())
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

    async def get_category_by_id(self, category_id: int) -> Category | None:
        statement = select(Category).where(Category.id == category_id)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

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

    async def list_sector_categories(self) -> list[Category]:
        """Return categories that have at least one product linked via product_sectors."""
        statement = (
            select(Category)
            .join(ProductSector, ProductSector.sector_id == Category.id)
            .join(Product, Product.id == ProductSector.product_id)
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

    async def delete_variant(self, variant: ProductVariant) -> None:
        await self.session.delete(variant)
        await self.session.flush()

    async def delete_image(self, image: ProductImage) -> None:
        await self.session.delete(image)
        await self.session.flush()

    async def flush(self) -> None:
        await self.session.flush()

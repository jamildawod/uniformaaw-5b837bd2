import csv
import hashlib
import json
import re
from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.logging import get_logger
from app.core.size import normalize_size
from app.core.text import slugify
from sqlalchemy import delete

from app.models.category import Category
from app.models.product import Product
from app.models.product_image import ProductImage
from app.models.product_sector import ProductSector
from app.models.product_variant import ProductVariant
from app.models.supplier import Supplier
from app.repositories.product_repository import ProductRepository
from app.schemas.sync import PimSyncResponse
from app.services.image_service import ImageService

CARE_TOKEN_MAP = {
    # Wash temperatures
    "wash_30": ("wash_30", ["wash_30", "tvatt30", "tvätt30", "30°", "30c", "30 c", "kall tvätt", "cold wash"]),
    "wash_40": ("wash_40", ["wash_40", "tvatt40", "tvätt40", "40°", "40c", "40 c"]),
    "wash_60": ("wash_60", ["wash_60", "tvatt60", "tvätt60", "60°", "60c", "60 c"]),
    "wash_95": ("wash_95", ["wash_95", "tvatt95", "tvätt95", "95°", "95c", "95 c", "koktvätt"]),
    # Hand wash
    "hand_wash": ("hand_wash", ["hand_wash", "handtvatt", "handtvätt", "hand wash", "tvätt för hand"]),
    # Bleach
    "no_bleach": ("no_bleach", ["no_bleach", "ingen blekning", "ej blekning", "no bleach", "bleach no"]),
    # Tumble dry
    "tumble_dry_low": ("tumble_dry_low", ["tumble_dry_low", "tumla låg", "tumla lag", "low tumble", "torktumla låg"]),
    "tumble_dry_medium": ("tumble_dry_medium", ["tumble_dry_medium", "tumla medel", "medium tumble", "torktumla medel"]),
    "no_tumble_dry": ("no_tumble_dry", ["no_tumble_dry", "ej tumla", "no tumble", "tumla ej", "tumla inte"]),
    # Iron
    "iron_low": ("iron_low", ["iron_low", "strykning låg", "lågvärme strykning", "iron low", "en punkt"]),
    "iron_medium": ("iron_medium", ["iron_medium", "strykning medel", "medelvarm strykning", "iron medium", "två punkter"]),
    "iron_high": ("iron_high", ["iron_high", "strykning hög", "högvärme strykning", "iron high", "tre punkter"]),
    "no_iron": ("no_iron", ["no_iron", "ej strykning", "stryk ej", "no iron", "stryk inte"]),
    # Dry clean
    "dry_clean": ("dry_clean", ["dry_clean", "kemtvätt", "dry clean", "kemisk tvätt"]),
    "no_dry_clean": ("no_dry_clean", ["no_dry_clean", "ej kemtvätt", "no dry clean"]),
}
ATTRIBUTE_ALIASES = {
    "fit": "Passform",
    "passform": "Passform",
    "weight": "Vikt",
    "vikt": "Vikt",
}
URL_PATTERN = re.compile(r"https?://\S+", re.IGNORECASE)

# Matches "65% polyester, 35% bomull", "50/50% bomull/polyester", "100% bomull", etc.
MATERIAL_PATTERN = re.compile(
    r"(\d{1,3}(?:\s*/\s*\d{1,3})?\s*%\s*\w+(?:[,/\s]+(?:och|and\s+)?\d{1,3}\s*%\s*\w+)*)",
    re.IGNORECASE | re.UNICODE,
)

# Fit terms: map lowercase variants to canonical Swedish label
FIT_TERMS: dict[str, str] = {
    "loose fit": "Loose fit",
    "regular fit": "Regular fit",
    "slim fit": "Slim fit",
    "relaxed fit": "Relaxed fit",
    "modern fit": "Modern fit",
    "classic fit": "Classic fit",
    "ledig passform": "Loose fit",
    "normal passform": "Regular fit",
    "smal passform": "Slim fit",
    "loose": "Loose fit",
    "regular": "Regular fit",
    "slim": "Slim fit",
    "relaxed": "Relaxed fit",
    "oversized": "Oversized",
}

# Canonical tag names — keyed by lowercase (with and without Swedish diacritics)
TAG_CANONICAL_MAP: dict[str, str] = {
    "dental": "Dental",
    "unisex": "Unisex",
    "hållbarhet": "Hållbarhet",
    "hallbarhet": "Hållbarhet",
    "vård": "Vård",
    "vard": "Vård",
    "städ": "Städ",
    "stad": "Städ",
    "kök": "Köket",
    "kok": "Köket",
    "köket": "Köket",
    "industri": "Industri",
    "restaurang": "Restaurang",
    "sjukvård": "Sjukvård",
    "sjukvard": "Sjukvård",
    "skola": "Skola",
    "hotell": "Hotell",
}

# Maps CSV IndustrySectorNames values (lowercased) to one of the 6 business-area root slugs.
# Values NOT listed here are considered unmappable (ambiguous or out-of-scope).
_SECTOR_TO_BUSINESS_AREA: dict[str, str] = {
    "dental": "dental",
    "djursjukvård": "djursjukvard",
    "djursjukvard": "djursjukvard",
    "apotek": "vard-omsorg",
    "vård": "vard-omsorg",
    "vard": "vard-omsorg",
    "vårdcentral": "vard-omsorg",
    "vardcentral": "vard-omsorg",
    "fysioterapi": "vard-omsorg",
    "hemtjänst": "vard-omsorg",
    "hemtjanst": "vard-omsorg",
    "healthcare": "vard-omsorg",
    "städ & service": "stad-service",
    "stad & service": "stad-service",
    "facility management": "stad-service",
    "lokalvård": "stad-service",
    "lokalvard": "stad-service",
    "lätt industri": "stad-service",
    "latt industri": "stad-service",
    "service": "stad-service",
    "restaurang, kök & café": "kok",
    "restaurang/café": "kok",
    "restaurang/cafe": "kok",
    "restaurang": "kok",
    "hotell": "kok",
    "hotell & restaurang": "kok",
    "food industry": "kok",
    "spa & beauty/wellness": "skonhet-halsa",
    "spa & beauty / wellness": "skonhet-halsa",
}

# Maps CSV ItemGroupName values (lowercased) to the child category type slug.
# Only item groups that unambiguously belong to one of the 5 child types are listed.
_ITEM_GROUP_TO_CHILD_SLUG: dict[str, str] = {
    # Byxor
    "fullängds byxor": "byxor",
    "fullangds byxor": "byxor",
    "3/4 byxor": "byxor",
    # Tunikor (tunikor, bussarong, väst)
    "v-halsad tunika/bussarong": "tunikor",
    "frontknäppt tunika med knappar": "tunikor",
    "frontknäppt tunika med dragkedja": "tunikor",
    "frontknappt tunika med knappar": "tunikor",
    "frontknappt tunika med dragkedja": "tunikor",
    "frontknäppt väst med knappar": "tunikor",
    "frontknäppt väst med dragkedja": "tunikor",
    "frontknappt vast med knappar": "tunikor",
    "frontknappt vast med dragkedja": "tunikor",
    "bussarong/tunika": "tunikor",
    "rundhalsad tunika/bussarong": "tunikor",
    "bussarong + byxa": "tunikor",
    # Rockar
    "labbrockar": "rockar",
    "kockrock - lång ärm": "rockar",
    "kockrock - lang arm": "rockar",
    "kockrock - kort ärm": "rockar",
    "kockrock - kort arm": "rockar",
    "3/4 ärm kockrock": "rockar",
    "3/4 arm kockrock": "rockar",
    "skyddsrock": "rockar",
    # Jackor
    "jackor": "jackor",
    "sweatshirtjackor": "jackor",
    "skaljackor": "jackor",
    "hoodies": "jackor",
    "kavajer": "jackor",
    "fleecejackor": "jackor",
    "friluftsjackor": "jackor",
    "vinterjackor": "jackor",
    "cardigan": "jackor",
    "cardigans": "jackor",
    # Accessoarer
    "kepsar och mössor": "accessoarer",
    "kepsar och mossor": "accessoarer",
    "kepsar/mössor": "accessoarer",
    "kepsar/mossor": "accessoarer",
    "mössor": "accessoarer",
    "mossor": "accessoarer",
    "scarfs": "accessoarer",
    "strumpor": "accessoarer",
    "skor": "accessoarer",
    "sneakers": "accessoarer",
    "sandal": "accessoarer",
    "toffel": "accessoarer",
    "namnskylt": "accessoarer",
    "huvudbonad": "accessoarer",
    "bandana": "accessoarer",
    "bälten och hängslen": "accessoarer",
    "balten och hangslen": "accessoarer",
    "id-hållare": "accessoarer",
    "id-hallare": "accessoarer",
    "nyckelband": "accessoarer",
    "pennhållare": "accessoarer",
    "pennhallare": "accessoarer",
    "väskor/ ryggsäckar": "accessoarer",
    "vaskor/ ryggsackar": "accessoarer",
    "väskor/ryggsäckar": "accessoarer",
    "vaskor/ryggsackar": "accessoarer",
}

# Pre-computed set of all hierarchical child category slugs to include in batch pre-fetch.
_HIERARCHICAL_CHILD_SLUGS: frozenset[str] = frozenset(
    f"{area}-{child}"
    for area in ("dental", "djursjukvard", "vard-omsorg", "stad-service", "kok", "skonhet-halsa")
    for child in ("byxor", "tunikor", "rockar", "jackor", "accessoarer")
)

# Hejco-specific sector fallback: maps ItemGroupName (lowercased) → canonical sector name.
# ONLY applied to Hejco products that have NO sector in the CSV (and are not VAS items).
# Rules are derived from 100% consistent evidence — every Hejco product with these item
# groups that has sector data maps exclusively to the stated sector.
# Do NOT add entries for item groups that have mixed sector evidence (e.g. byxor, tunikor).
_HEJCO_ITEM_GROUP_TO_SECTOR: dict[str, str] = {
    # Chef's coats → always restaurant/kitchen
    "kockrock - lång ärm": "Restaurang, kök & café",
    "kockrock - lang arm": "Restaurang, kök & café",
    "kockrock - kort ärm": "Restaurang, kök & café",
    "kockrock - kort arm": "Restaurang, kök & café",
    "3/4 ärm kockrock": "Restaurang, kök & café",
    "3/4 arm kockrock": "Restaurang, kök & café",
    # Aprons → always restaurant/kitchen
    "bröstförkläde": "Restaurang, kök & café",
    "brostforklade": "Restaurang, kök & café",
    "midjeförkläde": "Restaurang, kök & café",
    "midjeforklade": "Restaurang, kök & café",
    # Hats/caps — Hejco's range is exclusively for restaurant staff
    "kepsar och mössor": "Restaurang, kök & café",
    "kepsar och mossor": "Restaurang, kök & café",
    # Restaurant shirts/blouses
    "3/4 ärm skjortor/blusar": "Restaurang, kök & café",
    "3/4 arm skjortor/blusar": "Restaurang, kök & café",
    # Nurse watch — always healthcare
    "sjuksköterskeklocka": "Hemtjänst",
    "sjukskoterskeklocka": "Hemtjänst",
}


@dataclass(slots=True)
class VariantPayload:
    sku: str
    ean: str | None
    supplier_sku: str | None
    color: str | None
    size: str | None
    price: Decimal | None
    currency: str | None
    stock_quantity: int
    is_active: bool
    image_paths: list[str] = field(default_factory=list)


@dataclass(slots=True)
class ProductPayload:
    external_id: str
    name: str
    slug: str
    description: str | None
    brand: str | None
    material: str | None
    care_instructions: list[str] | None
    tags: list[str] | None
    certifications: list[str] | None
    qr_code: str | None
    attributes: dict[str, str] | None
    category_name: str | None
    is_active: bool
    # PIM visibility fields — sourced from IsSalesBlocked / ProductLifeCycleStatus
    is_sales_blocked: bool = False
    is_vas_item: bool = False  # IsVASItem=Yes → custom embroidery/print service, force sales-blocked
    lifecycle_status: str | None = None
    industry_sector_names: list[str] = field(default_factory=list)
    variants: list[VariantPayload] = field(default_factory=list)


@dataclass(slots=True)
class CsvReadResult:
    grouped: dict[str, ProductPayload]
    rows_processed: int = 0
    rows_failed: int = 0


class PimIngestionService:
    def __init__(
        self,
        session: AsyncSession,
        product_repository: ProductRepository,
        settings: Settings,
        image_service: ImageService | None = None,
    ) -> None:
        self.session = session
        self.product_repository = product_repository
        self.settings = settings
        self.image_service = image_service
        self.logger = get_logger(self.__class__.__name__)

    async def ingest(self) -> PimSyncResponse:
        csv_path = self.resolve_source_csv_path()
        supplier = await self.get_or_create_default_supplier()
        read_result = self._read_and_group(csv_path)
        response = PimSyncResponse(
            rows_processed=read_result.rows_processed,
            rows_failed=read_result.rows_failed,
        )
        external_ids = list(read_result.grouped.keys())
        run_seen_at = datetime.now(UTC)

        try:
            for start in range(0, len(external_ids), self.settings.pim_batch_size):
                batch_ids = external_ids[start : start + self.settings.pim_batch_size]
                batch_payloads = [read_result.grouped[external_id] for external_id in batch_ids]
                batch_result = await self._process_batch(batch_payloads, run_seen_at, supplier)
                response.products_created += batch_result.products_created
                response.products_updated += batch_result.products_updated
                response.products_unchanged += batch_result.products_unchanged
                response.variants_created += batch_result.variants_created
                response.variants_updated += batch_result.variants_updated
                response.variants_unchanged += batch_result.variants_unchanged
                response.images_discovered += batch_result.images_discovered
                response.sectors_assigned += batch_result.sectors_assigned
                response.sectors_missing += batch_result.sectors_missing
                await self.session.commit()

            deleted_at = datetime.now(UTC)
            await self.product_repository.soft_delete_missing_variants(run_seen_at, deleted_at)
            await self.product_repository.soft_delete_missing_products(run_seen_at, deleted_at)
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            self.logger.error(
                "PIM ingestion integrity error",
                extra={
                    "event": "pim_ingestion_integrity_error",
                    "error": str(exc),
                },
            )
            raise

        response.rows_created = response.products_created + response.variants_created
        response.rows_updated = response.products_updated + response.variants_updated
        self.logger.info(
            "PIM sync completed: products created=%s updated=%s unchanged=%s "
            "variants created=%s updated=%s unchanged=%s images discovered=%s "
            "sectors assigned=%s missing=%s (%.1f%% coverage)",
            response.products_created,
            response.products_updated,
            response.products_unchanged,
            response.variants_created,
            response.variants_updated,
            response.variants_unchanged,
            response.images_discovered,
            response.sectors_assigned,
            response.sectors_missing,
            (
                response.sectors_assigned
                / (response.sectors_assigned + response.sectors_missing)
                * 100
            )
            if (response.sectors_assigned + response.sectors_missing) > 0
            else 0.0,
        )
        return response

    def resolve_source_csv_path(self) -> Path:
        primary_path = self.settings.pim_csv_path
        if primary_path.exists():
            return primary_path

        search_dir = primary_path.parent
        fallback_candidates = sorted(
            {
                path
                for pattern in (primary_path.name, "PIMexport*.csv", "*.csv")
                for path in search_dir.glob(pattern)
                if path.is_file()
            },
            key=lambda path: path.stat().st_mtime,
            reverse=True,
        )
        if fallback_candidates:
            fallback = fallback_candidates[0]
            self.logger.warning(
                "Primary PIM CSV path missing; using fallback file %s",
                fallback,
            )
            return fallback

        raise FileNotFoundError(
            f"CSV file not found at {primary_path} and no fallback CSV was found in {search_dir}"
        )

    async def get_or_create_default_supplier(self) -> Supplier:
        supplier = await self.product_repository.get_supplier_by_code(self.settings.default_supplier_code)
        if supplier is not None:
            return supplier

        supplier = Supplier(
            code=self.settings.default_supplier_code,
            name=self.settings.default_supplier_name,
            is_active=True,
        )
        try:
            await self.product_repository.add_supplier(supplier)
            await self.session.flush()
            return supplier
        except IntegrityError:
            await self.session.rollback()
            existing = await self.product_repository.get_supplier_by_code(self.settings.default_supplier_code)
            if existing is None:
                raise
            return existing

    def _read_and_group(self, csv_path: Path) -> CsvReadResult:
        grouped: dict[str, ProductPayload] = {}
        seen_variant_keys: dict[str, set[tuple[str, str | None]]] = {}
        rows_processed = 0
        rows_failed = 0
        with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle, delimiter=self.settings.pim_csv_delimiter)
            headers = reader.fieldnames or []
            resolver = self._build_resolver(headers)

            for required in ("external_id", "name", "sku"):
                if required not in resolver:
                    raise ValueError(f"Missing required CSV column for {required}")

            for row in reader:
                rows_processed += 1
                external_id = self._get_value(row, resolver, "external_id")
                if not external_id:
                    rows_failed += 1
                    continue

                product = grouped.get(external_id)
                if product is None:
                    name = (
                        self._get_value(row, resolver, "name")
                        or self._get_value(row, resolver, "name_en")
                        or external_id
                    )
                    category_name = self._get_value(row, resolver, "category")
                    description = (
                        self._get_value(row, resolver, "description")
                        or self._get_value(row, resolver, "description_en")
                    )
                    material_value = self._resolve_material(row, resolver, description)
                    care_value = self._resolve_care_instructions(row, resolver)
                    tags_value = self._resolve_tags(row, resolver)
                    qr_value = self._resolve_qr_code(row, resolver)
                    certifications_value = self._resolve_certifications(row, resolver)
                    attributes_value = self._enrich_attributes_with_fit(
                        self._extract_attributes(row, resolver),
                        description,
                    )

                    raw_sectors = self._get_value(row, resolver, "industry_sectors")
                    sector_names = (
                        self._parse_sector_names(raw_sectors)
                        if raw_sectors
                        else []
                    )

                    # IsSalesBlocked in CSV is "Yes"/"No" string
                    raw_sales_blocked = self._get_value(row, resolver, "is_sales_blocked") or ""
                    is_sales_blocked = raw_sales_blocked.strip().lower() in {"yes", "true", "1", "ja"}

                    # IsVASItem=Yes means a customer-specific embroidery/print service item.
                    # These are not standard catalog products and must never be publicly visible.
                    raw_vas = self._get_value(row, resolver, "is_vas_item") or ""
                    is_vas_item = raw_vas.strip().lower() in {"yes", "true", "1", "ja"}
                    if is_vas_item:
                        is_sales_blocked = True

                    lifecycle_status = self._get_value(row, resolver, "lifecycle_status") or None

                    product = ProductPayload(
                        external_id=external_id,
                        name=name,
                        slug=slugify(f"{name}-{external_id}"),
                        description=description,
                        brand=self._get_value(row, resolver, "brand"),
                        material=material_value,
                        care_instructions=care_value,
                        tags=tags_value,
                        certifications=certifications_value,
                        qr_code=qr_value,
                        attributes=attributes_value,
                        category_name=category_name,
                        is_active=self._get_bool(row, resolver, "product_is_active", default=True),
                        is_sales_blocked=is_sales_blocked,
                        is_vas_item=is_vas_item,
                        lifecycle_status=lifecycle_status,
                        industry_sector_names=sector_names,
                    )
                    grouped[external_id] = product

                image_paths = self._get_image_paths(row, resolver)
                sku = self._get_value(row, resolver, "sku")
                if not sku:
                    rows_failed += 1
                    continue

                # Sizes column holds semicolon-separated list: "XS;M;L;XL"
                raw_sizes_field = self._get_value(row, resolver, "size")
                sizes_raw = [s.strip() for s in raw_sizes_field.split(";") if s.strip()] if raw_sizes_field else []

                # EANCodes column holds semicolon-separated list matching sizes by index
                raw_eans_field = self._get_value(row, resolver, "ean") or ""
                eans = [e.strip() for e in raw_eans_field.split(";") if e.strip()]

                color = self._get_value(row, resolver, "color")
                product_seen = seen_variant_keys.setdefault(external_id, set())

                # Expand one CSV row into one VariantPayload per size
                _VALID_SIZES = {"2XS","XS","S","M","L","XL","2XL","3XL","4XL","5XL","6XL"}

                for idx, raw_size in enumerate(sizes_raw if sizes_raw else [None]):
                    size = normalize_size(raw_size) if raw_size else None
                    if size not in _VALID_SIZES:
                        size = None

                    variant_key = (size, color.lower() if color else None)
                    if variant_key in product_seen:
                        continue
                    product_seen.add(variant_key)

                    ean = eans[idx] if idx < len(eans) else None
                    # Build unique SKU per variant: use EAN when available, else ItemNo-size
                    variant_sku = ean if ean else (f"{sku}-{size}" if size else sku)

                    product.variants.append(
                        VariantPayload(
                            sku=variant_sku,
                            ean=ean,
                            supplier_sku=sku.strip() if sku else None,
                            color=color,
                            size=size,
                            price=self._get_decimal(row, resolver, "price"),
                            currency=self._get_value(row, resolver, "currency"),
                            stock_quantity=self._get_stock_quantity(row, resolver),
                            is_active=self._get_bool(row, resolver, "variant_is_active", default=True),
                            image_paths=image_paths,
                        )
                    )
        return CsvReadResult(
            grouped=grouped,
            rows_processed=rows_processed,
            rows_failed=rows_failed,
        )

    def _build_resolver(self, headers: list[str]) -> dict[str, str]:
        normalized = {self._normalize_header(header): header for header in headers}
        aliases = {
            "external_id": ["external_id", "product_id", "style_no", "style", "artikelid", "artikelnummer", "ItemNo", "Id", "id"],
            "name": ["name", "product_name", "namn", "AdditionalName", "ENSOName"],
            "name_en": ["ENSOName"],
            "description": ["description", "produktbeskrivning", "beskrivning", "AdditionalDescription", "AdditionalWebText", "ENSODescription", "ENSOWebText"],
            "description_en": ["ENSODescription", "ENSOWebText"],
            "brand": ["brand", "varumarke", "varumärke", "BrandName"],
            "material": ["material", "materialsammansattning", "materialsammansättning", "AdditionalMaterialInfo", "ENSOMaterialInfo"],
            "care_instructions": ["care_instructions", "tvattrad", "tvättråd", "tvattråd", "wash_instructions", "WashGuideNames", "ENSOWashInfo", "AdditionalWashInfo"],
            "tags": ["tags", "etiketter", "taggar"],
            "certifications": ["certifications", "certifieringar", "certifikat", "CertificateFileUrls"],
            "qr_code": ["qr_code", "qr", "qr_url", "qr_link"],
            "category": ["category", "kategori", "category_name", "ItemGroupName", "itemgroupname", "item_group_name"],
            "industry_sectors": ["industry_sectors", "industrysectornames", "IndustrySectorNames", "sector", "sectors", "bransch"],
            "product_is_active": ["is_active", "active", "aktiv"],
            "sku": ["sku", "variant_sku", "artikelnummer_variant", "variantnummer", "ItemNo"],
            "ean": ["ean", "gtin", "streckkod", "EANCodes"],
            "color": ["color", "colour", "farg", "färg", "ColorNames"],
            "size": ["size", "storlek", "Sizes"],
            "price": ["price", "pris"],
            "currency": ["currency", "valuta"],
            "stock_quantity": ["stock_quantity", "lager", "stock", "inventory"],
            "variant_is_active": ["variant_active", "variant_is_active", "variant_aktiv"],
            "image_paths": ["image_paths", "images", "image", "bild", "bildvag", "ftp_path", "ftp_paths"],
            "is_sales_blocked": ["IsSalesBlocked", "is_sales_blocked", "sales_blocked", "salesblocked"],
            "is_vas_item": ["IsVASItem", "is_vas_item", "vasitem", "is_vas"],
            "lifecycle_status": ["ProductLifeCycleStatus", "lifecycle_status", "lifecyclestatus", "product_lifecycle_status"],
        }

        resolver: dict[str, str] = {}
        for canonical, candidates in aliases.items():
            for candidate in candidates:
                header = normalized.get(self._normalize_header(candidate))
                if header is not None:
                    resolver[canonical] = header
                    break
        return resolver

    def _compute_hash(self, data: dict[str, Any]) -> str:
        normalized = json.dumps(
            self._normalize_for_hash(data),
            sort_keys=True,
            separators=(",", ":"),
        )
        return hashlib.sha256(normalized.encode()).hexdigest()

    def _normalize_for_hash(self, value: Any) -> Any:
        if isinstance(value, Decimal):
            return format(value, "f")
        if isinstance(value, dict):
            return {key: self._normalize_for_hash(item) for key, item in value.items()}
        if isinstance(value, list):
            return [self._normalize_for_hash(item) for item in value]
        if value is None:
            return None
        return value

    async def _process_batch(
        self,
        payloads: list[ProductPayload],
        run_seen_at: datetime,
        supplier: Supplier,
    ) -> PimSyncResponse:
        result = PimSyncResponse()
        existing_products = await self.product_repository.get_by_external_ids(
            [payload.external_id for payload in payloads]
        )
        existing_variants = await self.product_repository.get_by_skus(
            [variant.sku for payload in payloads for variant in payload.variants]
        )
        category_names = [payload.category_name for payload in payloads if payload.category_name]
        category_slugs = list({slugify(name) for name in category_names} | _HIERARCHICAL_CHILD_SLUGS)
        categories = await self.product_repository.get_categories_by_slugs(category_slugs)

        all_sector_names = {
            name
            for payload in payloads
            for name in payload.industry_sector_names
        }
        sector_slugs = [slugify(name) for name in all_sector_names]
        sector_categories: dict[str, Category] = await self.product_repository.get_categories_by_slugs(sector_slugs)
        existing_images = await self.product_repository.get_images_by_external_paths(
            [
                image_path
                for payload in payloads
                for variant in payload.variants
                for image_path in variant.image_paths
            ]
        )
        downloaded_images: dict[str, str | None] = {}

        for payload in payloads:
            product = existing_products.get(payload.external_id)
            product_hash = self._compute_hash(
                {
                    "name": payload.name,
                    "slug": payload.slug,
                    "description": payload.description,
                    "brand": payload.brand,
                    "material": payload.material,
                    "care_instructions": payload.care_instructions,
                    "tags": payload.tags,
                    "certifications": payload.certifications,
                    "qr_code": payload.qr_code,
                    "attributes": payload.attributes,
                    "category": payload.category_name,
                    "is_active": payload.is_active,
                    "is_sales_blocked": payload.is_sales_blocked,
                    "lifecycle_status": payload.lifecycle_status,
                }
            )

            category = None
            if product is None or product.source_hash != product_hash:
                if payload.category_name:
                    # Attempt hierarchical resolution first (sector + item group → child category).
                    category = self._resolve_hierarchical_category(
                        categories,
                        payload.industry_sector_names,
                        payload.category_name,
                    )
                    if category is not None:
                        self.logger.debug(
                            "Hierarchical category resolved: product=%s → %s",
                            payload.external_id,
                            category.slug,
                        )
                    else:
                        # Fall back to flat category lookup / auto-create.
                        category_slug = slugify(payload.category_name)
                        category = await self._resolve_category(
                            categories, category_slug, payload.category_name
                        )

            if product is None:
                product = Product(
                    external_id=payload.external_id,
                    source_hash=product_hash,
                    name=payload.name,
                    slug=payload.slug,
                    description=payload.description,
                    brand=payload.brand,
                    material=payload.material,
                    care_instructions=payload.care_instructions,
                    tags=payload.tags,
                    certifications=payload.certifications,
                    qr_code=payload.qr_code,
                    attributes=payload.attributes,
                    category_id=category.id if category else None,
                    supplier_id=supplier.id,
                    is_active=payload.is_active,
                    is_sales_blocked=payload.is_sales_blocked,
                    lifecycle_status=payload.lifecycle_status,
                    last_seen_at=run_seen_at,
                    deleted_at=None,
                )
                await self.product_repository.add_product(product)
                await self.session.flush()
                existing_products[payload.external_id] = product
                result.products_created += 1
            elif product.source_hash == product_hash:
                product.last_seen_at = run_seen_at
                product.deleted_at = None
                result.products_unchanged += 1
            else:
                changed = self._update_if_changed(
                    product,
                    {
                        "name": payload.name,
                        "slug": payload.slug,
                        "description": payload.description,
                        "brand": payload.brand,
                        "material": payload.material,
                        "care_instructions": payload.care_instructions,
                        "tags": payload.tags,
                        "certifications": payload.certifications,
                        "qr_code": payload.qr_code,
                        "attributes": payload.attributes,
                        "category_id": category.id if category else None,
                        "supplier_id": supplier.id,
                        "is_active": payload.is_active,
                        "is_sales_blocked": payload.is_sales_blocked,
                        "lifecycle_status": payload.lifecycle_status,
                        "last_seen_at": run_seen_at,
                        "deleted_at": None,
                        "source_hash": product_hash,
                    },
                )
                if changed:
                    result.products_updated += 1
                else:
                    result.products_unchanged += 1

            # Apply Hejco fallback when CSV has no sector data for non-VAS products.
            effective_sector_names = payload.industry_sector_names
            if not effective_sector_names and not payload.is_vas_item and supplier.code == "hejco":
                effective_sector_names = self._resolve_hejco_sector_fallback(payload.category_name)
                if effective_sector_names:
                    self.logger.debug(
                        "[SECTOR_FALLBACK] product_id=%s external_id=%s item_group=%r → %s",
                        product.id,
                        payload.external_id,
                        payload.category_name,
                        effective_sector_names,
                    )

            await self._sync_product_sectors(product, effective_sector_names, sector_categories)
            if effective_sector_names:
                result.sectors_assigned += 1
            else:
                result.sectors_missing += 1

            for index, variant_payload in enumerate(payload.variants):
                variant_hash = self._compute_hash(
                    {
                        "ean": variant_payload.ean,
                        "color": variant_payload.color,
                        "size": variant_payload.size,
                        "price": variant_payload.price,
                        "currency": variant_payload.currency,
                        "stock_quantity": variant_payload.stock_quantity,
                        "is_active": variant_payload.is_active,
                    }
                )
                variant = existing_variants.get(variant_payload.sku)

                if variant is None:
                    variant = ProductVariant(
                        product_id=product.id,
                        sku=variant_payload.sku,
                        supplier_sku=variant_payload.supplier_sku,
                        source_hash=variant_hash,
                        ean=variant_payload.ean,
                        color=variant_payload.color,
                        size=variant_payload.size,
                        price=variant_payload.price,
                        currency=variant_payload.currency,
                        stock_quantity=variant_payload.stock_quantity,
                        is_active=variant_payload.is_active,
                        last_seen_at=run_seen_at,
                        deleted_at=None,
                    )
                    await self.product_repository.add_variant(variant)
                    await self.session.flush()
                    existing_variants[variant_payload.sku] = variant
                    result.variants_created += 1
                elif variant.source_hash == variant_hash:
                    changed = self._update_if_changed(
                        variant,
                        {
                            "product_id": product.id,
                            "last_seen_at": run_seen_at,
                            "deleted_at": None,
                        },
                    )
                    # Backfill supplier_sku if it was never set (zero-downtime migration).
                    if variant.supplier_sku is None and variant_payload.supplier_sku:
                        variant.supplier_sku = variant_payload.supplier_sku
                        changed = True
                    if changed:
                        result.variants_updated += 1
                    else:
                        result.variants_unchanged += 1
                else:
                    changed = self._update_if_changed(
                        variant,
                        {
                            "product_id": product.id,
                            "supplier_sku": variant_payload.supplier_sku,
                            "ean": variant_payload.ean,
                            "color": variant_payload.color,
                            "size": variant_payload.size,
                            "price": variant_payload.price,
                            "currency": variant_payload.currency,
                            "stock_quantity": variant_payload.stock_quantity,
                            "is_active": variant_payload.is_active,
                            "last_seen_at": run_seen_at,
                            "deleted_at": None,
                            "source_hash": variant_hash,
                        },
                    )
                    if changed:
                        result.variants_updated += 1
                    else:
                        result.variants_unchanged += 1

                for image_index, image_path in enumerate(variant_payload.image_paths):
                    existing_image = existing_images.get(image_path)
                    if existing_image is not None:
                        if (
                            existing_image.local_path is None
                            and self.image_service is not None
                            and self._is_http_url(image_path)
                        ):
                            existing_image.local_path = await self._download_http_image_once(
                                image_path,
                                downloaded_images,
                            )
                        self._update_if_changed(
                            existing_image,
                            {
                                "product_id": product.id,
                                "variant_id": variant.id,
                                "is_primary": image_index == 0 and index == 0,
                                "sort_order": image_index,
                            },
                        )
                        continue

                    local_path = None
                    if self.image_service is not None and self._is_http_url(image_path):
                        local_path = await self._download_http_image_once(image_path, downloaded_images)

                    image = ProductImage(
                        product_id=product.id,
                        variant_id=variant.id,
                        external_path=image_path,
                        local_path=local_path,
                        is_primary=image_index == 0 and index == 0,
                        sort_order=image_index,
                    )
                    await self.product_repository.add_image(image)
                    existing_images[image_path] = image
                    result.images_discovered += 1

        return result

    async def _download_http_image_once(
        self,
        image_path: str,
        downloaded_images: dict[str, str | None],
    ) -> str | None:
        if image_path not in downloaded_images:
            downloaded_images[image_path] = await self.image_service.download_http_image(image_path)
        return downloaded_images[image_path]

    def _resolve_hierarchical_category(
        self,
        categories: dict[str, Category],
        sector_names: list[str],
        item_group_name: str | None,
    ) -> Category | None:
        """Return the matching hierarchical child category, or None if ambiguous/unmapped.

        Resolution succeeds only when:
        - All sector names map to exactly one business area, AND
        - The item group name maps to one of the 5 child types (byxor/tunikor/rockar/jackor/accessoarer).
        """
        if not sector_names or not item_group_name:
            return None

        business_areas: set[str] = set()
        for name in sector_names:
            area = _SECTOR_TO_BUSINESS_AREA.get(name.lower().strip())
            if area:
                business_areas.add(area)

        if len(business_areas) != 1:
            return None

        child_slug = _ITEM_GROUP_TO_CHILD_SLUG.get(item_group_name.lower().strip())
        if not child_slug:
            return None

        business_area = next(iter(business_areas))
        return categories.get(f"{business_area}-{child_slug}")

    async def _resolve_category(
        self,
        categories: dict[str, Category],
        category_slug: str,
        category_name: str,
    ) -> Category:
        category = categories.get(category_slug)
        if category is None:
            existing = await self.product_repository.get_categories_by_slugs([category_slug])
            category = existing.get(category_slug)

        if category is None:
            try:
                async with self.session.begin_nested():
                    category = Category(name=category_name, slug=category_slug)
                    await self.product_repository.add_category(category)
                    await self.session.flush()
            except IntegrityError:
                existing = await self.product_repository.get_categories_by_slugs([category_slug])
                category = existing.get(category_slug)

        if category is None:
            raise ValueError(f"Could not resolve category for slug {category_slug}")

        categories[category_slug] = category
        return category

    @staticmethod
    def _parse_sector_names(raw: str) -> list[str]:
        """Parse a raw sector field value into a deduplicated list of sector name strings.

        Handles:
        - Semicolon-separated values (primary format: "Dental;Djursjukvård")
        - Pipe-separated values as fallback ("|")
        - Strips whitespace from each value
        - Deduplicates case-insensitively while preserving original casing of first occurrence
        """
        # Split on ";" first; fall back to "|" if no ";" found
        delimiter = ";" if ";" in raw else "|"
        parts = [s.strip() for s in raw.split(delimiter) if s.strip()]

        # Deduplicate: keep first occurrence per lowercased name
        seen: dict[str, str] = {}
        for part in parts:
            key = part.lower()
            if key not in seen:
                seen[key] = part
        return list(seen.values())

    @staticmethod
    def _resolve_hejco_sector_fallback(item_group_name: str | None) -> list[str]:
        """Return a fallback sector name list for a Hejco product with no CSV sector data.

        Only called when:
        - supplier.code == "hejco"
        - industry_sector_names is empty
        - is_vas_item is False

        Returns a single-element list with the canonical sector name if the item group
        matches a high-confidence rule in _HEJCO_ITEM_GROUP_TO_SECTOR, otherwise [].
        """
        if not item_group_name:
            return []
        sector = _HEJCO_ITEM_GROUP_TO_SECTOR.get(item_group_name.lower().strip())
        return [sector] if sector else []

    async def _sync_product_sectors(
        self,
        product: Product,
        sector_names: list[str],
        sector_categories: dict[str, Category],
    ) -> None:
        """Replace the product's sector links with those from the current CSV row."""
        if not sector_names:
            self.logger.debug(
                "[SECTOR_MISSING] product_id=%s external_id=%s",
                product.id,
                product.external_id,
            )
            # Still run the delete so stale links from a previous run are cleaned up
            await self.session.execute(
                delete(ProductSector).where(ProductSector.product_id == product.id)
            )
            self.session.expire(product, ["sectors"])
            return

        target_sector_ids: set[int] = set()
        for name in sector_names:
            slug = slugify(name)
            sector_cat = sector_categories.get(slug)
            if sector_cat is None:
                existing = await self.product_repository.get_categories_by_slugs([slug])
                sector_cat = existing.get(slug)

            if sector_cat is None:
                try:
                    async with self.session.begin_nested():
                        sector_cat = Category(name=name, slug=slug)
                        await self.product_repository.add_category(sector_cat)
                        await self.session.flush()
                except IntegrityError:
                    existing = await self.product_repository.get_categories_by_slugs([slug])
                    sector_cat = existing.get(slug)

            if sector_cat is None:
                raise ValueError(f"Could not resolve sector category for slug {slug}")

            sector_categories[slug] = sector_cat
            target_sector_ids.add(sector_cat.id)

        self.logger.debug(
            "[SECTOR_ASSIGNED] product_id=%s external_id=%s sectors=%s",
            product.id,
            product.external_id,
            sector_names,
        )

        # Delete existing sector links then reinsert
        await self.session.execute(
            delete(ProductSector).where(ProductSector.product_id == product.id)
        )
        # Expire the ORM collection so SQLAlchemy doesn't re-insert stale rows on next flush
        self.session.expire(product, ["sectors"])
        for sector_id in target_sector_ids:
            self.session.add(ProductSector(product_id=product.id, sector_id=sector_id))

    def _update_if_changed(self, model: object, values: dict[str, object]) -> bool:
        changed = False
        for field_name, value in values.items():
            if getattr(model, field_name) != value:
                setattr(model, field_name, value)
                changed = True
        return changed

    def _normalize_header(self, value: str) -> str:
        return "".join(char for char in value.lower() if char.isalnum() or char == "_")

    @staticmethod
    def _is_http_url(value: str) -> bool:
        return value.startswith("http://") or value.startswith("https://")

    def _get_value(self, row: dict[str, str], resolver: dict[str, str], field: str) -> str | None:
        header = resolver.get(field)
        if header is None:
            return None
        value = row.get(header)
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None

    def _get_int(self, row: dict[str, str], resolver: dict[str, str], field: str) -> int:
        value = self._get_value(row, resolver, field)
        if value is None:
            return 0
        try:
            return int(value)
        except ValueError:
            return 0

    def _get_stock_quantity(self, row: dict[str, str], resolver: dict[str, str]) -> int:
        header = resolver.get("stock_quantity")
        if header is None:
            return 100

        value = row.get(header)
        if value is None:
            return 100

        stripped = value.strip()
        if not stripped:
            return 100

        try:
            return int(stripped)
        except ValueError:
            return 0

    def _get_decimal(self, row: dict[str, str], resolver: dict[str, str], field: str) -> Decimal | None:
        value = self._get_value(row, resolver, field)
        if value is None:
            return None
        try:
            return Decimal(value.replace(",", "."))
        except InvalidOperation:
            return None

    def _get_bool(
        self,
        row: dict[str, str],
        resolver: dict[str, str],
        field: str,
        default: bool,
    ) -> bool:
        value = self._get_value(row, resolver, field)
        if value is None:
            return default
        return value.lower() in {"1", "true", "yes", "ja", "y"}

    def _get_image_paths(self, row: dict[str, str], resolver: dict[str, str]) -> list[str]:
        value = self._get_value(row, resolver, "image_paths")
        if value is None:
            return []
        return [item.strip() for item in value.replace("|", ",").replace(";", ",").split(",") if item.strip()]

    def _parse_tags(self, value: str | None) -> list[str] | None:
        if value is None:
            return None
        raw_tags = [item.strip() for item in re.split(r"[|,;]", value) if item.strip()]
        normalized: list[str] = []
        for tag in raw_tags:
            lower = tag.lower()
            # Strip diacritics for fallback lookup
            ascii_lower = (
                lower.replace("å", "a").replace("ä", "a").replace("ö", "o")
            )
            canonical = TAG_CANONICAL_MAP.get(lower) or TAG_CANONICAL_MAP.get(ascii_lower)
            normalized.append(canonical if canonical else tag)
        return list(dict.fromkeys(normalized)) or None

    def _parse_care_instructions(self, value: str | None) -> list[str] | None:
        if value is None:
            return None
        normalized = value.strip().lower()
        tokens: list[str] = []
        for code, patterns in CARE_TOKEN_MAP.values():
            if any(pattern in normalized for pattern in patterns):
                tokens.append(code)
        return list(dict.fromkeys(tokens)) or None

    def _parse_certifications(self, value: str | None) -> list[str] | None:
        if value is None:
            return None
        normalized = value.strip().lower()
        tokens: list[str] = []
        if any(t in normalized for t in ["oeko", "oeko-tex", "öko-tex", "oeko tex", "standard 100"]):
            tokens.append("oeko_tex")
        if "gots" in normalized:
            tokens.append("gots")
        if "bluesign" in normalized:
            tokens.append("bluesign")
        if "fairtrade" in normalized or "fair trade" in normalized:
            tokens.append("fairtrade")
        return tokens or None

    def _parse_material_from_description(self, description: str | None) -> str | None:
        if not description:
            return None
        match = MATERIAL_PATTERN.search(description)
        return match.group(1).strip() if match else None

    def _parse_fit_from_description(self, description: str | None) -> str | None:
        if not description:
            return None
        lower = description.lower()
        # Check longer terms first to avoid partial matches (e.g. "slim" in "slim fit")
        for term in sorted(FIT_TERMS, key=len, reverse=True):
            if term in lower:
                return FIT_TERMS[term]
        return None

    def _enrich_attributes_with_fit(
        self,
        attributes: dict[str, str] | None,
        description: str | None,
    ) -> dict[str, str] | None:
        """Add Passform to attributes from description if not already present."""
        fit_keys = {"passform", "fit"}
        already_has_fit = attributes and any(
            k.lower() in fit_keys for k in attributes
        )
        if already_has_fit:
            return attributes
        fit = self._parse_fit_from_description(description)
        if not fit:
            return attributes
        result = dict(attributes) if attributes else {}
        result["Passform"] = fit
        return result

    def _resolve_material(
        self,
        row: dict[str, str],
        resolver: dict[str, str],
        description: str | None = None,
    ) -> str | None:
        explicit = self._first_non_empty(
            self._get_value(row, resolver, "material"),
            row.get("ENSOMaterialInfo"),
            row.get("AdditionalMaterialInfo"),
            row.get("Material"),
            row.get("Materialbeskrivning"),
            row.get("Kvalitet"),
            row.get("Composition"),
        )
        if explicit:
            return explicit
        return self._parse_material_from_description(description)

    def _resolve_care_instructions(
        self,
        row: dict[str, str],
        resolver: dict[str, str],
    ) -> list[str] | None:
        care_raw = self._first_non_empty(
            self._get_value(row, resolver, "care_instructions"),
            row.get("WashGuideNames"),
            row.get("ENSOWashInfo"),
            row.get("AdditionalWashInfo"),
            row.get("Tvättråd"),
            row.get("Skötselråd"),
            row.get("Care"),
            row.get("Washing"),
        )
        return self._parse_care_instructions(care_raw)

    def _resolve_tags(
        self,
        row: dict[str, str],
        resolver: dict[str, str],
    ) -> list[str] | None:
        tags_raw = self._first_non_empty(
            self._get_value(row, resolver, "tags"),
            row.get("Taggar"),
            row.get("Tags"),
            row.get("Kategori"),
            row.get("Användning"),
        )
        return self._parse_tags(tags_raw)

    def _resolve_certifications(
        self,
        row: dict[str, str],
        resolver: dict[str, str],
    ) -> list[str] | None:
        cert_raw = self._first_non_empty(
            self._get_value(row, resolver, "certifications"),
            row.get("CertificateFileUrls"),
            row.get("Certifiering"),
            row.get("OekoTex"),
            row.get("Standard"),
        )
        return self._parse_certifications(cert_raw)

    def _resolve_qr_code(
        self,
        row: dict[str, str],
        resolver: dict[str, str],
    ) -> str | None:
        qr_raw = self._first_non_empty(
            self._get_value(row, resolver, "qr_code"),
            row.get("QR"),
            row.get("QR Code"),
            row.get("QrUrl"),
        )
        return self._extract_url(qr_raw)

    def _extract_url(self, value: str | None) -> str | None:
        if value is None:
            return None
        match = URL_PATTERN.search(value)
        return match.group(0) if match else None

    def _first_non_empty(self, *values: str | None) -> str | None:
        for value in values:
            if value is None:
                continue
            stripped = value.strip()
            if stripped:
                return stripped
        return None

    def _extract_attributes(
        self,
        row: dict[str, str],
        resolver: dict[str, str],
    ) -> dict[str, str] | None:
        used_headers = set(resolver.values())
        attributes: dict[str, str] = {}
        for header, raw_value in row.items():
            if header in used_headers or raw_value is None:
                continue
            value = raw_value.strip()
            if not value:
                continue
            normalized_header = self._normalize_header(header)
            label = None
            if normalized_header.startswith("attribute_"):
                label = header.split("_", 1)[1].strip() or header
            elif normalized_header.startswith("attr_"):
                label = header.split("_", 1)[1].strip() or header
            elif normalized_header in ATTRIBUTE_ALIASES:
                label = ATTRIBUTE_ALIASES[normalized_header]

            if label:
                attributes[label] = value
        return attributes or None

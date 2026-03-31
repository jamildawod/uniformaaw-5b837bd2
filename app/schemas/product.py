import os
import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, computed_field, field_validator, model_validator


_STORAGE_IMAGES_ROOT = "/opt/uniforma/storage/images"


def _media_file_exists(suffix: str) -> bool:
    """Return True if the file exists on disk under the storage/images mount."""
    disk_path = os.path.join(_STORAGE_IMAGES_ROOT, suffix.lstrip("/"))
    return os.path.exists(disk_path)


_BAD_ARTICLE_NUMBER_FRAGMENTS = ("xl", "xs", "s-", "m-", "l-", "--")


def is_clean_article_number(value: str | None) -> bool:
    if value is None:
        return False

    trimmed = value.strip()
    if not trimmed:
        return False

    if trimmed.isdigit() and len(trimmed) > 10:
        return False

    lowered = trimmed.lower()
    if any(fragment in lowered for fragment in _BAD_ARTICLE_NUMBER_FRAGMENTS):
        return False

    return True


def get_clean_article_number(value: str | None) -> str | None:
    if not is_clean_article_number(value):
        return None
    return value.strip()


class AutocompleteItem(BaseModel):
    label: str
    value: str
    slug: str
    id: str
    image_url: str | None = None
    category: str | None = None
    is_fallback: bool = False


class CategoryRead(BaseModel):
    id: int
    name: str
    slug: str
    image: str | None = None
    parent_id: int | None

    model_config = ConfigDict(from_attributes=True)


class ProductImageRead(BaseModel):
    id: int
    variant_id: int | None
    external_path: str
    local_path: str | None
    is_primary: bool
    sort_order: int

    model_config = ConfigDict(from_attributes=True)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def url(self) -> str:
        if self.local_path:
            # Already a full HTTP/HTTPS URL or a confirmed servable /uploads/ path
            if self.local_path.startswith(("http://", "https://", "/uploads/")):
                return self.local_path
            # local_path is a /media/ URL-style path — only return it if the file
            # actually exists under the storage/images mount; otherwise fall through
            # to external_path so we never return a 404 URL.
            if self.local_path.startswith("/media/"):
                suffix = self.local_path[len("/media/"):]
                if _media_file_exists(suffix):
                    return self.local_path
                # File missing — fall through to external_path below
            else:
                # Absolute disk path containing /images/ storage marker
                # e.g. /opt/uniforma/storage/images/https/host/path.webp → https://host/path.webp
                marker = "/images/"
                idx = self.local_path.find(marker)
                if idx != -1:
                    suffix = self.local_path[idx + len(marker):]
                    if suffix.startswith("https/"):
                        return "https://" + suffix[len("https/"):]
                    if suffix.startswith("http/"):
                        # Files downloaded from external URLs are stored under http/
                        # but the CDN serves them over https. Prefer external_path
                        # (already a valid https:// URL) over reconstructing http://.
                        ep = self.external_path
                        if ep and (ep.startswith("https://") or ep.startswith("http://")):
                            return ep
                        return "http://" + suffix[len("http/"):]
                    # Non-http/https local storage image — only return /media/ URL if
                    # the file actually exists on disk; otherwise fall through.
                    if _media_file_exists(suffix):
                        return f"/media/{suffix}"
                    # File missing — fall through to external_path below
                else:
                    # Absolute disk path containing /uploads/ storage marker
                    # e.g. /opt/uniforma/storage/uploads/products/file.webp → /uploads/products/file.webp
                    marker2 = "/uploads/"
                    idx2 = self.local_path.find(marker2)
                    if idx2 != -1:
                        return f"/uploads/{self.local_path[idx2 + len(marker2):]}"
        ep = self.external_path or ""
        # Full HTTP/HTTPS URL — return directly when no local copy yet
        if ep.startswith("http://") or ep.startswith("https://"):
            return ep
        if not ep:
            return "/images/placeholder.webp"
        # Relative external_path has no guaranteed mount — return placeholder
        # rather than a broken /media/ URL.
        return "/images/placeholder.webp"


class ProductVariantRead(BaseModel):
    id: int
    sku: str
    ean: str | None
    color: str | None
    size: str | None
    price: Decimal | None
    currency: str | None
    stock_quantity: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    images: list[ProductImageRead] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class ProductRead(BaseModel):
    id: uuid.UUID
    external_id: str
    article_number: str | None = None
    name: str
    slug: str
    description: str | None
    brand: str | None
    material: str | None = None
    fit: str | None = None
    care_instructions: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    certifications: list[str] = Field(default_factory=list)
    qr_code: str | None = None
    attributes: dict[str, str] | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    category: CategoryRead | None = None
    images: list[ProductImageRead] = Field(default_factory=list)
    variants: list[ProductVariantRead] = Field(default_factory=list)
    price: Decimal | None = None

    model_config = ConfigDict(from_attributes=True)

    @field_validator("care_instructions", "tags", mode="before")
    @classmethod
    def ensure_list(cls, v: object) -> list:
        if v is None:
            return []
        if isinstance(v, list):
            return v
        return []

    @field_validator("certifications", mode="before")
    @classmethod
    def normalize_certifications(cls, v: object) -> list[str]:
        """Accept both legacy dict format and new string-token format."""
        if v is None:
            return []
        if not isinstance(v, list):
            return []
        tokens: list[str] = []
        for item in v:
            if isinstance(item, str):
                tokens.append(item)
            elif isinstance(item, dict):
                # Backward compat: convert old {name, label, qr} dicts to tokens
                name = (item.get("name") or "").lower()
                if "oeko" in name or "öko" in name:
                    tokens.append("oeko_tex")
                elif "gots" in name:
                    tokens.append("gots")
                elif "bluesign" in name:
                    tokens.append("bluesign")
                elif "fairtrade" in name:
                    tokens.append("fairtrade")
        return list(dict.fromkeys(tokens))

    @computed_field  # type: ignore[prop-decorator]
    @property
    def primary_image(self) -> str | None:
        """Best available image URL: direct images → variant images → None."""
        for img in self.images:
            return img.url
        for variant in self.variants:
            for img in variant.images:
                return img.url
        return None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def item_no(self) -> str | None:
        return get_clean_article_number(self.external_id)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def image_url(self) -> str | None:
        return self.primary_image

    @computed_field  # type: ignore[prop-decorator]
    @property
    def image(self) -> str | None:
        return self.primary_image

    @model_validator(mode="after")
    def compute_derived(self) -> "ProductRead":
        self.article_number = get_clean_article_number(self.external_id)
        # Compute price from active variants
        if self.price is None and self.variants:
            prices = [
                v.price
                for v in self.variants
                if v.price is not None and v.is_active
            ]
            if prices:
                self.price = min(prices)
        # Extract fit from attributes and remove Passform key so it doesn't
        # appear again in the Specifikation block on the frontend.
        if self.attributes:
            fit_keys = {"Passform", "passform", "Fit", "fit"}
            for key in fit_keys:
                if key in self.attributes and self.fit is None:
                    self.fit = self.attributes[key]
            cleaned = {k: val for k, val in self.attributes.items() if k not in fit_keys}
            self.attributes = cleaned or None
        return self


class AdminOverridePatchRequest(BaseModel):
    overrides: dict[str, str | int | float | bool | None]


class AdminProductUpdateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    price: Decimal = Field(..., ge=0)
    category_id: int | None = Field(default=None, ge=1)
    is_active: bool

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        trimmed = value.strip()
        if not trimmed:
            raise ValueError("Name cannot be blank.")
        return trimmed

    @field_validator("description")
    @classmethod
    def normalize_description(cls, value: str | None) -> str | None:
        if value is None:
            return None
        trimmed = value.strip()
        return trimmed or None


class AdminVariantUpdateRequest(BaseModel):
    sku: str = Field(..., min_length=1, max_length=128)
    ean: str | None = Field(default=None, max_length=64)
    color: str | None = Field(default=None, max_length=64)
    size: str | None = Field(default=None, max_length=64)
    price: Decimal | None = Field(default=None, ge=0)
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    stock_quantity: int = Field(..., ge=0)
    is_active: bool

    @field_validator("sku")
    @classmethod
    def validate_sku(cls, value: str) -> str:
        trimmed = value.strip()
        if not trimmed:
            raise ValueError("SKU cannot be blank.")
        return trimmed

    @field_validator("ean", "color", "size")
    @classmethod
    def normalize_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        trimmed = value.strip()
        return trimmed or None

    @field_validator("currency")
    @classmethod
    def normalize_currency(cls, value: str | None) -> str | None:
        if value is None:
            return None
        trimmed = value.strip().upper()
        return trimmed or None


class AdminImageCreateRequest(BaseModel):
    external_path: str
    local_path: str | None = None
    variant_id: int | None = None
    is_primary: bool = False
    sort_order: int = 0


class AdminImageReorderRequest(BaseModel):
    image_ids: list[int] = Field(default_factory=list)


class AdminProductRead(ProductRead):
    applied_overrides: dict[str, str | int | float | bool | list | dict | None] = Field(
        default_factory=dict,
    )
    sectors: list[str] = Field(default_factory=list)


class FiltersRead(BaseModel):
    colors: list[str]
    sizes: list[str]
    categories: list[CategoryRead]

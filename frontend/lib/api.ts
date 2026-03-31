import type { Filters, Product } from "./types";
import {
  applyProductOverrides,
  getProductImage,
  getItemNo,
  isVisibleStorefrontProduct,
  type ProductOverrides,
} from "./product-utils";

export interface AutocompleteItem {
  /** Product name */
  label: string;
  /** supplier_sku / ItemNo */
  value: string;
  slug: string;
  id: string;
  name?: string;
  ENSOName?: string;
  itemNo?: string;
  ItemNo?: string;
  category?: string | null;
  categoryPath?: string | null;
  imageUrl?: string | null;
  images?: Array<
    | string
    | {
        url?: string | null;
        local_path?: string | null;
        external_path?: string | null;
      }
  >;
  ImageNames?: string[] | null;
}

// NEXT_PUBLIC_API_URL must include /api/v1 (e.g. https://api.uniforma.livosys.se/api/v1)
export const API_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "https://api.uniforma.livosys.se/api/v1";
export const SUPER_DEALS_URL =
  process.env.NEXT_PUBLIC_SUPER_DEALS_URL ??
  "https://admin-uniforma.livosys.se/api/v1/super-deals";
export const PRODUCT_OVERRIDES_URL =
  process.env.NEXT_PUBLIC_PRODUCT_OVERRIDES_URL ??
  "https://admin-uniforma.livosys.se/api/v1/admin/product-overrides";

// Origin only, for constructing image URLs that are served outside /api/v1
export const API_ORIGIN = API_URL.replace(/\/api\/v1\/?$/, "");

export function imageUrl(path: string): string {
  if (!path) return "/placeholder.jpg";
  try {
    // If it's already an absolute URL, return as-is
    new URL(path);
    return path;
  } catch {
    // Root-relative path like /uploads/foo.jpg — attach to origin
    return `${API_ORIGIN}${path}`;
  }
}

export interface SuperDeal {
  id: number | string;
  title: string;
  description: string | null;
  image_url: string | null;
  pdf_url: string | null;
  price_text: string | null;
  article_number: string | null;
  active: boolean;
  source_type: string | null;
  source_file_name: string | null;
  stock_total: number | null;
  sizes: string[] | null;
}

type ProductVisibilityValue = string | number | boolean | null | undefined;

type ProductWithVisibility = Product & {
  ItemNo?: string | null;
  itemNo?: string | null;
  lifecycle_status?: string | null;
  ProductLifeCycleStatus?: string | null;
  is_sales_blocked?: boolean | string | null;
  IsSalesBlocked?: boolean | string | null;
  attributes?: Record<string, ProductVisibilityValue> | null;
};

function getProductItemNo(product: ProductWithVisibility): string | null {
  const candidates = [
    product.ItemNo,
    product.item_no,
    product.itemNo,
  ];

  for (const candidate of candidates) {
    if (typeof candidate === "string" && candidate.trim()) {
      return candidate.trim();
    }
  }

  return null;
}

export async function fetchProductOverrides(): Promise<ProductOverrides> {
  try {
    const res = await fetch(PRODUCT_OVERRIDES_URL, {
      cache: "no-store",
    });
    if (!res.ok) return {};

    const data = await res.json();
    return data && typeof data === "object" ? (data as ProductOverrides) : {};
  } catch {
    return {};
  }
}

function extractProducts(data: unknown): ProductWithVisibility[] {
  if (Array.isArray(data)) return data as ProductWithVisibility[];
  if (Array.isArray((data as { data?: unknown[] })?.data)) {
    return (data as { data: ProductWithVisibility[] }).data;
  }
  if (Array.isArray((data as { items?: unknown[] })?.items)) {
    return (data as { items: ProductWithVisibility[] }).items;
  }
  return [];
}

function extractSuperDeals(data: unknown): Record<string, unknown>[] {
  if (Array.isArray(data)) {
    return data.filter(
      (item): item is Record<string, unknown> => Boolean(item) && typeof item === "object",
    );
  }
  if (Array.isArray((data as { data?: unknown[] })?.data)) {
    return (data as { data: unknown[] }).data.filter(
      (item): item is Record<string, unknown> => Boolean(item) && typeof item === "object",
    );
  }
  if (Array.isArray((data as { items?: unknown[] })?.items)) {
    return (data as { items: unknown[] }).items.filter(
      (item): item is Record<string, unknown> => Boolean(item) && typeof item === "object",
    );
  }
  return [];
}

function normalizeSuperDeal(item: Record<string, unknown>): SuperDeal | null {
  const rawTitle = item.title;
  const rawId = item.id;

  if (
    (typeof rawId !== "number" && typeof rawId !== "string") ||
    typeof rawTitle !== "string" ||
    !rawTitle.trim()
  ) {
    return null;
  }

  const rawActive =
    item.active === true || item.is_active === true;

  return {
    id: rawId,
    title: rawTitle.trim(),
    description: typeof item.description === "string" ? item.description : null,
    image_url:
      typeof item.image_url === "string" && item.image_url.trim()
        ? imageUrl(item.image_url)
        : null,
    pdf_url:
      typeof item.pdf_url === "string" && item.pdf_url.trim()
        ? item.pdf_url
        : null,
    price_text:
      typeof item.price_text === "string" && item.price_text.trim()
        ? item.price_text
        : null,
    article_number:
      typeof item.article_number === "string" && item.article_number.trim()
        ? item.article_number.trim()
        : null,
    active: rawActive,
    source_type:
      typeof item.source_type === "string" ? item.source_type : null,
    source_file_name:
      typeof item.source_file_name === "string" ? item.source_file_name : null,
    stock_total:
      typeof item.stock_total === "number" ? item.stock_total : null,
    sizes: Array.isArray(item.sizes)
      ? item.sizes.filter((size): size is string => typeof size === "string")
      : null,
  };
}

function getVisibilityField(
  product: ProductWithVisibility,
  keys: string[],
): ProductVisibilityValue {
  for (const key of keys) {
    const value = product[key as keyof ProductWithVisibility];
    if (value !== undefined && value !== null) return value as ProductVisibilityValue;
  }

  const attributes = product.attributes;
  if (!attributes) return undefined;

  for (const key of keys) {
    const value = attributes[key];
    if (value !== undefined && value !== null) return value;
  }

  return undefined;
}

function isSalesBlocked(value: ProductVisibilityValue): boolean {
  if (typeof value === "boolean") return value;
  if (typeof value === "number") return value !== 0;
  if (typeof value === "string") {
    return ["true", "1", "yes", "ja"].includes(value.trim().toLowerCase());
  }
  return false;
}

export function isVisibleProduct(product: ProductWithVisibility): boolean {
  const itemNo = getProductItemNo(product);
  const lifecycleStatus = getVisibilityField(product, [
    "lifecycle_status",
    "ProductLifeCycleStatus",
  ]);
  const normalizedStatus =
    typeof lifecycleStatus === "string"
      ? lifecycleStatus.trim().toLowerCase() === "active"
        ? "Active"
        : lifecycleStatus.trim()
      : "";

  return Boolean(itemNo) && normalizedStatus === "Active";
}

async function fetchProductBatch(params: {
  limit: number;
  offset: number;
  category?: string;
  color?: string;
  size?: string;
  sector?: string;
}): Promise<ProductWithVisibility[]> {
  const query = new URLSearchParams();
  query.set("limit", String(params.limit));
  if (params.offset) query.set("offset", String(params.offset));
  if (params.category) query.set("category", params.category);
  if (params.color) query.set("color", params.color);
  if (params.size) query.set("size", params.size);
  if (params.sector) query.set("sector", params.sector);

  const res = await fetch(`${API_URL}/products?${query.toString()}`, {
    next: { revalidate: 60 },
  });
  if (!res.ok) return [];

  const data = await res.json();
  return extractProducts(data);
}

export async function fetchProducts(params: {
  limit?: number;
  offset?: number;
  category?: string;
  color?: string;
  size?: string;
  sector?: string;
}): Promise<Product[]> {
  try {
    const overrides = await fetchProductOverrides();
    const visibleOffset = params.offset ?? 0;
    const visibleLimit = params.limit ?? 200;
    const targetVisibleCount = visibleOffset + visibleLimit;
    const batchSize = Math.max(visibleLimit, 100);
    const visibleProducts: ProductWithVisibility[] = [];
    let rawOffset = 0;

    while (visibleProducts.length < targetVisibleCount) {
      const batch = await fetchProductBatch({
        limit: batchSize,
        offset: rawOffset,
        category: params.category,
        color: params.color,
        size: params.size,
        sector: params.sector,
      });

      if (batch.length === 0) break;

      visibleProducts.push(
        ...batch
          .map((product) => applyProductOverrides(product, overrides))
          .filter((product) => isVisibleProduct(product) && isVisibleStorefrontProduct(product)),
      );
      rawOffset += batch.length;

      if (batch.length < batchSize) break;
    }

    return visibleProducts.slice(visibleOffset, targetVisibleCount);
  } catch {
    return [];
  }
}

export async function fetchSuperDeals(): Promise<SuperDeal[]> {
  try {
    const res = await fetch(SUPER_DEALS_URL, {
      cache: "no-store",
    });
    if (!res.ok) {
      console.error("Failed to fetch super deals");
      return [];
    }

    const data = await res.json();
    const deals = extractSuperDeals(data)
      .map(normalizeSuperDeal)
      .filter((deal): deal is SuperDeal => deal !== null)
      .filter((deal) => deal.active === true);

    console.log("SUPER DEALS:", deals);
    return deals;
  } catch {
    return [];
  }
}

export async function fetchProduct(slug: string): Promise<Product | null> {
  try {
    const res = await fetch(`${API_URL}/products/${slug}`, {
      next: { revalidate: 60 },
    });
    if (res.status === 404) return null;
    if (!res.ok) return null;
    const product = await res.json();
    const overrides = await fetchProductOverrides();
    const visibleProduct = applyProductOverrides(product, overrides);

    if (!isVisibleStorefrontProduct(visibleProduct)) {
      return null;
    }

    return {
      ...visibleProduct,
      image: getProductImage(visibleProduct),
      itemNo: getItemNo(visibleProduct),
      ItemNo: visibleProduct.ItemNo ?? getItemNo(visibleProduct),
      item_no: visibleProduct.item_no ?? getItemNo(visibleProduct),
    };
  } catch {
    return null;
  }
}

export async function fetchFilters(): Promise<Filters> {
  try {
    const res = await fetch(`${API_URL}/filters`, {
      next: { revalidate: 300 },
    });
    if (!res.ok) return { colors: [], sizes: [], categories: [] };
    const data = await res.json();
    return {
      colors: Array.isArray(data?.colors) ? data.colors : [],
      sizes: Array.isArray(data?.sizes) ? data.sizes : [],
      categories: Array.isArray(data?.categories) ? data.categories : [],
    };
  } catch {
    return { colors: [], sizes: [], categories: [] };
  }
}

export async function fetchAutocomplete(q: string, limit = 8): Promise<AutocompleteItem[]> {
  const trimmed = q.trim();
  if (!trimmed) return [];
  try {
    const params = new URLSearchParams({ q: trimmed, limit: String(limit) });
    const res = await fetch(`${API_URL}/products/autocomplete?${params.toString()}`, {
      cache: "no-store",
    });
    if (!res.ok) return [];
    const data = await res.json();
    if (!Array.isArray(data)) return [];

    return data
      .map((item): AutocompleteItem | null => {
        if (!item || typeof item !== "object") return null;

        const record = item as Record<string, unknown>;
        const label =
          typeof record.label === "string"
            ? record.label
            : typeof record.ENSOName === "string"
              ? record.ENSOName
              : "";
        const value =
          typeof record.value === "string"
            ? record.value
            : typeof record.ItemNo === "string"
              ? record.ItemNo
              : "";
        const slug = typeof record.slug === "string" ? record.slug : "";
        const id =
          typeof record.id === "string"
            ? record.id
            : typeof record.slug === "string"
              ? record.slug
              : `${label}-${value}`;

        if (!label || !slug) return null;

        return {
          label,
          value,
          slug,
          id,
          name:
            typeof record.name === "string"
              ? record.name
              : typeof record.ENSOName === "string"
                ? record.ENSOName
                : undefined,
          ENSOName:
            typeof record.ENSOName === "string" ? record.ENSOName : undefined,
          itemNo:
            typeof record.itemNo === "string"
              ? record.itemNo
              : typeof record.ItemNo === "string"
                ? record.ItemNo
                : undefined,
          ItemNo:
            typeof record.ItemNo === "string" ? record.ItemNo : undefined,
          category:
            typeof record.category === "string"
              ? record.category
              : typeof (record.category as { name?: unknown } | null)?.name === "string"
                ? ((record.category as { name: string }).name ?? null)
                : null,
          categoryPath:
            typeof record.categoryPath === "string"
              ? record.categoryPath
              : typeof record.category_path === "string"
                ? record.category_path
                : null,
          imageUrl:
            typeof record.imageUrl === "string"
              ? record.imageUrl
              : typeof record.image_url === "string"
                ? record.image_url
                : typeof record.primary_image === "string"
                  ? record.primary_image
                  : null,
          images: Array.isArray(record.images)
            ? (record.images as AutocompleteItem["images"])
            : undefined,
          ImageNames: Array.isArray(record.ImageNames)
            ? (record.ImageNames as string[])
            : null,
        };
      })
      .filter((item): item is AutocompleteItem => Boolean(item));
  } catch {
    return [];
  }
}

export async function fetchCategories(): Promise<
  Array<{ id: number; name: string; slug: string; parent_id: number | null; sector_slug: string | null; image: string | null }>
> {
  try {
    const res = await fetch(`${API_URL}/categories`, {
      next: { revalidate: 300 },
    });
    if (!res.ok) return [];
    const data = await res.json();
    return Array.isArray(data)
      ? data
      : Array.isArray(data?.data)
        ? data.data
        : [];
  } catch {
    return [];
  }
}

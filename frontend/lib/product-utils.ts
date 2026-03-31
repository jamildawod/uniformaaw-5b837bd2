export type ProductOverride = {
  is_hidden?: boolean;
  hide_image?: boolean;
};

export type ProductOverrides = Record<string, ProductOverride>;

export function getItemNo(product: any): string {
  if (product.ItemNo) {
    return product.ItemNo;
  }

  if (product.item_no) {
    return product.item_no;
  }

  throw new Error("Missing ItemNo");
}

export function tryGetItemNo(product: any): string | null {
  try {
    return getItemNo(product);
  } catch {
    return null;
  }
}

export function getBaseItemNo(product: any): string {
  const itemNo = getItemNo(product);

  return itemNo.split("-")[0];
}

export function getProductCategory(product: any) {

  if (product.category) {
    if (typeof product.category === "string") {
      return product.category.toLowerCase();
    }

    if (product.category.name) {
      return `${String(product.category.name).toLowerCase()} ${String(product.category.slug).toLowerCase()}`;
    }

    if (product.category.slug) {
      return String(product.category.slug).toLowerCase();
    }
  }

  if (product.category_name) {
    return String(product.category_name).toLowerCase();
  }

  if (product.category_path) {
    return String(product.category_path).toLowerCase();
  }

  if (product.categories && product.categories.length > 0) {
    const firstCategory = product.categories[0];

    if (typeof firstCategory === "string") {
      return firstCategory.toLowerCase();
    }

    if (firstCategory.name) {
      return `${String(firstCategory.name).toLowerCase()} ${String(firstCategory.slug).toLowerCase()}`;
    }

    if (firstCategory.slug) {
      return String(firstCategory.slug).toLowerCase();
    }
  }

  if (product.group) {
    return String(product.group).toLowerCase();
  }

  if (product.segment) {
    return String(product.segment).toLowerCase();
  }

  return "";
}

export function normalizeCategorySlug(category: string) {
  const value = category
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "");

  if (value.includes("dental")) return "dental";
  if (value.includes("djursjukvard")) return "djursjukvard";
  if (value.includes("kok")) return "restaurang";
  if (value.includes("restaurang")) return "restaurang";
  if (value.includes("skonhet")) return "spa";
  if (value.includes("beauty")) return "spa";
  if (value.includes("spa")) return "spa";
  if (value.includes("stad")) return "stad";
  if (value.includes("vard")) return "vard";

  return value;
}

export function isActiveProduct(product: any): boolean {
  const status =
    product?.ProductLifeCycleStatus ||
    product?.product_life_cycle_status ||
    product?.lifecycle_status ||
    product?.status ||
    "";
  if (String(status).toLowerCase() === "active") return true;
  // API returns is_active boolean when no lifecycle status field exists
  if (!status && product?.is_active === true) return true;
  return false;
}

export function applyProductOverrides(
  product: any,
  overrides: ProductOverrides = {},
) {
  const itemNo = tryGetItemNo(product);
  const override = itemNo ? overrides[itemNo] || {} : {};
  const isHidden = override.is_hidden === true || product?.is_hidden === true;
  const hideImage = override.hide_image === true || product?.hide_image === true;

  return {
    ...product,
    ...(itemNo
      ? {
          itemNo,
          ItemNo: product?.ItemNo ?? itemNo,
          item_no: product?.item_no ?? itemNo,
        }
      : {}),
    is_hidden: isHidden,
    hide_image: hideImage,
    ...(hideImage
      ? {
          image: "",
          image_url: "",
          primary_image: "",
          images: [],
          media: [],
          pictures: [],
          variants: Array.isArray(product?.variants)
            ? product.variants.map((variant: any) => ({
                ...variant,
                images: [],
              }))
            : product?.variants,
        }
      : {}),
  };
}

export function isVisibleStorefrontProduct(product: any): boolean {
  return Boolean(tryGetItemNo(product)) && isActiveProduct(product) && !product?.is_hidden;
}

export function normalizeStorefrontProduct(product: any) {
  const overridden = applyProductOverrides(product);
  const itemNo = getItemNo(overridden);
  const lifecycleStatus = overridden.ProductLifeCycleStatus
    ? String(overridden.ProductLifeCycleStatus).toLowerCase()
    : overridden.is_active === true
      ? "active"
      : "";
  const image = getProductImage(overridden);

  return {
    ...overridden,
    id: itemNo,
    image,
    item_no: itemNo,
    itemNo,
    ItemNo: itemNo,
    ProductLifeCycleStatus: lifecycleStatus,
  };
}

export function filterStorefrontProducts(
  products: any[],
  overrides: ProductOverrides = {},
) {
  return products
    .map((p: any) => applyProductOverrides(p, overrides))
    .filter((p: any) => isVisibleStorefrontProduct(p))
    .map((p: any) => {
      const itemNo = tryGetItemNo(p);

      return {
        ...p,
        itemNo: itemNo ?? p.itemNo,
        image: getProductImage(p),
      };
    });
}

export function filterHomepageProducts(
  products: any[],
  overrides: ProductOverrides = {},
) {
  return filterStorefrontProducts(products, overrides).filter((product: any) => {
    return hasProductImage(product);
  });
}

export function dedupeProducts(products: any[]) {
  const map = new Map();

  for (const product of products) {
    const itemNo = getItemNo(product);
    const existing = map.get(itemNo);

    if (!map.has(itemNo)) {
      map.set(itemNo, product);
      continue;
    }

    if (!hasProductImage(existing) && hasProductImage(product)) {
      map.set(itemNo, product);
    }
  }

  return Array.from(map.values());
}

export function groupProducts(products: any[]) {
  const map = new Map();

  for (const entry of products) {
    const product = normalizeStorefrontProduct(entry);
    const base = getBaseItemNo(product);

    if (!map.has(base)) {
      map.set(base, {
        ...product,
        id: getItemNo(product),
        baseItemNo: base,
        variants: [product],
      });
    } else {
      map.get(base).variants.push(product);
    }
  }

  return Array.from(map.values());
}

export function getProductImage(product: any): string {
  if (product?.hide_image) return "";

  const raw =
    product.image ||
    product.image_url ||
    product.primary_image ||
    (product.images && product.images.length > 0
      ? product.images[0].url || product.images[0]
      : null) ||
    (product.media && product.media.length > 0
      ? product.media[0].url
      : null) ||
    (product.pictures && product.pictures.length > 0
      ? product.pictures[0]
      : null) ||
    null;
  return toAbsoluteUrl(raw);
}

export function resolveProductImage(product: any): string {
  return toAbsoluteUrl(getProductImage(product));
}

export function hasProductImage(product: any): boolean {
  const image = getProductImage(product);

  if (!image) return false;
  if (typeof image === "string" && image.trim() === "") return false;
  // Ignore placeholder — not a real product image
  if (typeof image === "string" && image.startsWith("/images/placeholder")) return false;

  return true;
}

export function resolveImageUrl(image: any): string {
  if (typeof image === "string") {
    return toAbsoluteUrl(image);
  }

  if (image.url) {
    return toAbsoluteUrl(image.url);
  }

  return "/placeholder.png";
}

export function toAbsoluteUrl(url?: string | null): string {
  if (!url) return "";

  if (url.startsWith("http")) return url;

  // Local Next.js static assets — don't prepend external domain
  if (url.startsWith("/images/") || url.startsWith("/public/")) return url;

  return `https://uniforma.livosys.se${url}`;
}

export function cleanName(name: string): string {
  return String(name || "")
    .replace(/hejco/gi, "")
    .replace(/\s+/g, " ")
    .trim();
}

import type { StoreProduct } from "@/components/ProductCard";

export const ALLOWED_SIZES = [
  "2XS",
  "XS",
  "S",
  "M",
  "L",
  "XL",
  "2XL",
  "3XL",
  "4XL",
  "5XL",
  "6XL",
] as const;

export function normalizeSize(value?: string | null): string | null {
  if (!value) return null;

  const normalized = value.trim().toUpperCase();

  if (normalized === "XXS") return "2XS";
  if (normalized === "XXL") return "2XL";

  if (ALLOWED_SIZES.includes(normalized as (typeof ALLOWED_SIZES)[number])) {
    return normalized;
  }

  // Pass through numeric and non-standard sizes instead of dropping them
  return normalized;
}

export function getAvailableSizes(products: StoreProduct[]): string[] {
  const seen = new Set<string>();

  for (const product of products) {
    for (const variant of product.variants ?? []) {
      const normalized = normalizeSize(variant.size);
      if (normalized) {
        seen.add(normalized);
      }
    }
  }

  return ALLOWED_SIZES.filter((size) => seen.has(size));
}

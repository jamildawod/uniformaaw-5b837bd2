import type { Filters, Product } from "./types";

// NEXT_PUBLIC_API_URL must include /api/v1 (e.g. https://api.uniforma.livosys.se/api/v1)
export const API_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "https://api.uniforma.livosys.se/api/v1";

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

export async function fetchProducts(params: {
  limit?: number;
  offset?: number;
  category?: string;
  color?: string;
  size?: string;
}): Promise<Product[]> {
  try {
    const query = new URLSearchParams();
    query.set("limit", String(params.limit ?? 200));
    if (params.offset) query.set("offset", String(params.offset));
    if (params.category) query.set("category", params.category);
    if (params.color) query.set("color", params.color);
    if (params.size) query.set("size", params.size);

    const res = await fetch(`${API_URL}/products?${query.toString()}`, {
      next: { revalidate: 60 },
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

export async function fetchProduct(slug: string): Promise<Product | null> {
  try {
    const res = await fetch(`${API_URL}/products/${slug}`, {
      next: { revalidate: 60 },
    });
    if (res.status === 404) return null;
    if (!res.ok) return null;
    return res.json();
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

export async function fetchCategories(): Promise<
  Array<{ id: number; name: string; slug: string; parent_id: number | null }>
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

"use client";

import Image from "next/image";
import Link from "next/link";
import { cleanName, getItemNo, getProductImage } from "@/lib/product-utils";

const BLUR_DATA_URL =
  "data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIzMDAiIGhlaWdodD0iMzAwIiB2aWV3Qm94PSIwIDAgMzAwIDMwMCI+PHJlY3Qgd2lkdGg9IjMwMCIgaGVpZ2h0PSIzMDAiIGZpbGw9IiNmNWVmZTYiLz48L3N2Zz4=";

export const COLOR_MAP: Record<string, string> = {
  svart: "#000000",
  vit: "#ffffff",
  grå: "#9ca3af",
  blå: "#2563eb",
  röd: "#dc2626",
  grön: "#16a34a",
  beige: "#d6d3d1",
  marin: "#1e3a8a",
  navy: "#1e3a8a",
  gul: "#facc15",
  rosa: "#f472b6",
}

export function cleanColorName(color: string): string {
  if (!color) return ""
  return color.split(" ").slice(-1)[0].toLowerCase()
}

export type StoreImageLike = StoreImage | string;

export type StoreImage = {
  id: number;
  external_path: string;
  local_path: string | null;
  is_primary: boolean;
  sort_order: number;
  url?: string | null;
};

export type StoreVariant = {
  id: number;
  sku?: string;
  color: string | null;
  size: string | null;
  price: number | string | null;
  currency: string | null;
  stock_quantity?: number;
  is_active?: boolean;
  images: StoreImageLike[];
};

export type StoreProduct = {
  id: string;
  baseItemNo?: string;
  ItemNo?: string | null;
  itemNo?: string | null;
  article_number?: string | null;
  item_no?: string | null;
  external_id?: string;
  image?: string | null;
  image_url?: string | null;
  name: string;
  slug: string;
  description: string | null;
  brand: string | null;
  material: string | null;
  fit: string | null;
  care_instructions: string[];
  tags: string[];
  certifications: string[];
  qr_code: string | null;
  attributes: Record<string, string> | null;
  price?: string | number | null;
  primary_image?: string | null;
  category: {
    id: number;
    name: string;
    slug: string;
    parent_id: number | null;
  } | null;
  images: StoreImageLike[];
  variants: StoreVariant[];
  category_slug?: string | null;
  colors?: string[];
  sizes?: string[];
};

export function ProductCard({ product, isTopMatch }: { product: StoreProduct; isTopMatch?: boolean }) {
  const displayProduct =
    product.baseItemNo && Array.isArray(product.variants) && product.variants.length > 0
      ? (product.variants[0] as any)
      : product;
  const itemNo = getItemNo(displayProduct);
  const variantCount = Array.isArray(product.variants) ? product.variants.length : 0;
  const safeName = cleanName(product.name) || "Uniforma";
  const image = getProductImage(product);

  console.log("PRODUCT DEBUG:", product);
  console.log("ITEMNO:", itemNo);

  return (
    <Link
      href={`/product/${itemNo}`}
      className="relative group bg-white border border-gray-200 rounded-xl p-4 text-center shadow-sm hover:shadow-md transition-all duration-200 flex flex-col"
    >
      {isTopMatch && (
        <div className="absolute top-2 left-2 bg-black text-white text-xs px-2 py-1 rounded z-10">
          Bästa match
        </div>
      )}

      <div className="flex justify-center mb-4">
        <div className="relative w-32 h-32 rounded-full bg-[#f5efe6] flex items-center justify-center overflow-hidden flex-shrink-0">
          {image && (
            <Image
              src={image}
              alt={itemNo}
              fill
              className="object-contain p-[5%]"
              loading={isTopMatch ? undefined : "lazy"}
              priority={Boolean(isTopMatch)}
              placeholder="blur"
              blurDataURL={BLUR_DATA_URL}
              sizes="(max-width: 768px) 50vw, (max-width: 1200px) 33vw, 25vw"
              onError={(e) => { e.currentTarget.src = "/images/placeholder.webp"; }}
            />
          )}
        </div>
      </div>

      <h3 className="text-sm font-medium text-gray-800 mb-1 line-clamp-2 leading-snug">
        {safeName}
      </h3>

      <p className="text-xs text-gray-400 mb-2">Art.nr: {itemNo}</p>
      {variantCount > 0 && (
        <p className="text-xs text-gray-500 mb-2">{variantCount} varianter</p>
      )}

      <div className="mt-auto">
        <span className="inline-block bg-blue-500 text-white text-xs px-4 py-2 rounded-md group-hover:bg-blue-600 transition">
          Läs mer
        </span>
      </div>
    </Link>
  );
}

export default ProductCard;

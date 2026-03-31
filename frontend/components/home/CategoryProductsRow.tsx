"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { fetchProducts } from "@/lib/api";
import { ProductCard } from "@/components/ProductCard";
import type { StoreProduct } from "@/components/ProductCard";
import {
  filterHomepageProducts,
  getItemNo,
  getProductCategory,
  normalizeCategorySlug,
} from "@/lib/product-utils";

type Category = {
  id: number;
  name: string;
  slug: string;
};

export function CategoryProductsRow({ category }: { category: Category }) {
  const [products, setProducts] = useState<StoreProduct[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;
    fetchProducts({ category: category.slug, limit: 6 }).then((data) => {
      if (active) {
        const categorySlug = normalizeCategorySlug(category.slug.toLowerCase());
        const filteredProducts = filterHomepageProducts(data as any[]).filter((p: any) => {
          const productCategory = getProductCategory(p);

          console.log("CATEGORY MATCH:", {
            category: category.slug,
            productCategory,
          });

          return productCategory.includes(categorySlug);
        });

        setProducts(filteredProducts as StoreProduct[]);
        setLoading(false);
      }
    });
    return () => {
      active = false;
    };
  }, [category.slug]);

  // Don't render the section at all if no products came back
  if (!loading && (products || []).length === 0) return null;

  return (
    <section className="mx-auto max-w-6xl px-4 py-8">
      <div className="mb-4 flex items-end justify-between">
        <h2 className="text-xl font-bold tracking-tight text-stone-950">
          {category.name}
        </h2>
        <Link
          href={`/shop?category=${encodeURIComponent(category.slug)}`}
          className="text-sm font-semibold text-stone-500 transition hover:text-stone-950"
        >
          Visa alla
        </Link>
      </div>

      {loading ? (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 sm:gap-6 lg:grid-cols-3 xl:grid-cols-4">
          {Array.from({ length: 6 }).map((_, i) => (
            <div
              key={i}
              className="bg-white border border-gray-200 rounded-lg p-3 flex flex-col gap-2 animate-pulse"
            >
              <div className="aspect-square bg-gray-200 rounded" />
              <div className="h-3 bg-gray-200 rounded w-1/2 mx-auto" />
              <div className="h-4 bg-gray-200 rounded w-3/4 mx-auto" />
              <div className="h-6 bg-gray-200 rounded w-16 mx-auto" />
            </div>
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 sm:gap-6 lg:grid-cols-3 xl:grid-cols-4">
          {(products || []).map((product) => {
            const itemNo = getItemNo(product as any);
            if (!itemNo) return null;
            return <ProductCard key={itemNo} product={product} />;
          })}
        </div>
      )}
    </section>
  );
}

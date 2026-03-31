"use client"

import { safeArray } from "@/components/SafeArray"
import Link from "next/link"
import { ProductCard } from "@/components/ProductCard"
import { filterHomepageProducts, getItemNo } from "@/lib/product-utils"

export function ProductSection({ title, ctaLabel, href, products }: any) {
  const safeProducts = filterHomepageProducts(safeArray(products))

  return (
    <section className="max-w-6xl mx-auto px-4 py-10 sm:py-16">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-semibold">{title}</h2>
        {ctaLabel && href && (
          <Link href={href} className="text-sm text-gray-500 hover:text-black">
            {ctaLabel}
          </Link>
        )}
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 sm:gap-6 lg:grid-cols-3 xl:grid-cols-4">
        {(safeProducts || []).filter(Boolean).map((p: any) => {
          const itemNo = getItemNo(p)
          if (!itemNo) return null
          return <ProductCard key={itemNo} product={p} />
        })}
      </div>
    </section>
  )
}

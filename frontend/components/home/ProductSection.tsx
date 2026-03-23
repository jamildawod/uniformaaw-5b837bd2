"use client"

import { safeArray } from "@/components/SafeArray"
import Link from "next/link"

export function ProductSection({ title, ctaLabel, href, products }: any) {
  const safeProducts = safeArray(products)

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
        {(safeProducts || []).map((p: any) => (
          <Link key={p.id} href={`/product/${p.slug}`}>
            <div className="border rounded-xl p-3 hover:shadow-sm transition">
              <div className="aspect-square bg-gray-100 rounded mb-3 overflow-hidden">
                {p?.images?.[0]?.url && (
                  <img
                    src={p.images[0].url}
                    className="w-full h-full object-cover"
                  />
                )}
              </div>
              <p className="text-sm font-medium">{p.name}</p>
            </div>
          </Link>
        ))}
      </div>
    </section>
  )
}

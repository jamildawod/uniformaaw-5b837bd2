"use client"

import Link from "next/link"
import Image from "next/image"
import { safeArray } from "@/components/SafeArray"
import type { Product } from "@/lib/types"
import { filterHomepageProducts, getItemNo, getProductImage } from "@/lib/product-utils"

interface Props {
  title?: string
  products?: Product[]
}

export function CategorySection({ title, products }: Props) {
  const filtered = filterHomepageProducts(safeArray(products))
  const items = filtered.slice(0, 8)

  return (
    <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16 md:py-20">
      {title && (
        <div className="mb-8 flex items-center justify-between">
          <h2 className="text-xl font-semibold text-gray-900">{title}</h2>
          <a href="/shop" className="text-sm font-medium text-gray-500 hover:text-gray-900 transition-colors">
            Visa alla →
          </a>
        </div>
      )}

      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6 md:gap-8">
        {items.map((item: any) => {
          const src = getProductImage(item)
          const itemNo = getItemNo(item)

          const card = (
            <div className="group rounded-2xl border border-gray-100 bg-white overflow-hidden shadow-sm hover:shadow-md hover:-translate-y-0.5 transition-all duration-200 cursor-pointer">
              <div className="aspect-[4/3] bg-gray-50 overflow-hidden relative">
                {src && (
                  <Image
                    src={src}
                    alt={item.name}
                    fill
                    className="object-contain p-4 group-hover:scale-105 transition-transform duration-300"
                    unoptimized
                  />
                )}
              </div>
              <div className="p-5">
                <p className="text-base font-semibold text-gray-900 line-clamp-2 leading-snug">{item.name}</p>
                <p className="mt-1 text-sm text-gray-500">Läs mer →</p>
              </div>
            </div>
          )

          return itemNo ? (
            <Link key={itemNo} href={`/product/${itemNo}`}>
              {card}
            </Link>
          ) : null
        })}
      </div>
    </section>
  )
}

"use client"

import { useState } from "react"
import { ProductCard, StoreProduct, COLOR_MAP, cleanColorName } from "@/components/ProductCard"
import { filterStorefrontProducts, getItemNo } from "@/lib/product-utils"

function normalizeColor(color: string): string {
  const c = color.toLowerCase()
  if (c.includes("svart")) return "svart"
  if (c.includes("vit")) return "vit"
  if (c.includes("grå") || c.includes("grey")) return "grå"
  if (c.includes("blå") || c.includes("navy") || c.includes("marin")) return "blå"
  if (c.includes("röd")) return "röd"
  if (c.includes("grön")) return "grön"
  if (c.includes("beige")) return "beige"
  return "övrig"
}

interface ShopFiltersProps {
  products: StoreProduct[]
  allColors: string[]
  allSizes: string[]
  sector?: string
  category?: string
  query?: string
}

export function ShopFilters({
  products,
  allColors,
  allSizes,
  sector,
  category,
  query,
}: ShopFiltersProps) {
  const [selectedColor, setSelectedColor] = useState<string | null>(null)
  const [selectedSize, setSelectedSize] = useState<string | null>(null)
  const visibleProducts = filterStorefrontProducts(products as any[]) as StoreProduct[]

  const filteredProducts = visibleProducts.filter((product) => {
    const variants = product.variants || []

    const matchesColor =
      !selectedColor || variants.some((v) => normalizeColor(v.color || "") === selectedColor)

    const matchesSize =
      !selectedSize || variants.some((v) => v.size === selectedSize)

    return matchesColor && matchesSize
  })

  return (
    <div className="grid grid-cols-1 md:grid-cols-[220px_1fr] gap-8">
      {/* Filter sidebar */}
      <aside className="text-sm space-y-6">
        {/* Kategori */}
        <div>
          <h3 className="font-semibold mb-2 text-gray-800">Kategori</h3>
          <div className="space-y-1">
            {[
              { label: "Alla", href: "/shop" },
              { label: "Byxor", href: "/shop?category=byxor" },
              { label: "Jackor", href: "/shop?category=jackor" },
              { label: "Tunikor", href: "/shop?category=tunika" },
              { label: "Skjortor", href: "/shop?category=skjortor" },
              { label: "Tröjor", href: "/shop?category=trojor" },
            ].map(({ label, href }) => (
              <a
                key={href}
                href={href}
                className={`block py-1 px-2 rounded hover:bg-gray-100 transition ${
                  category && href.includes(category)
                    ? "font-semibold text-black"
                    : "text-gray-600"
                }`}
              >
                {label}
              </a>
            ))}
          </div>
        </div>

        {/* Bransch */}
        <div>
          <h3 className="font-semibold mb-2 text-gray-800">Bransch</h3>
          <div className="space-y-1">
            {[
              { label: "Dental", href: "/shop?sector=dental" },
              { label: "Vård & Omsorg", href: "/shop?sector=vard" },
              { label: "Kök & Restaurang", href: "/shop?sector=kok" },
              { label: "Skönhet & Hälsa", href: "/shop?sector=beauty" },
              { label: "Städ & Service", href: "/shop?sector=stad" },
              { label: "Djursjukvård", href: "/shop?sector=djursjukvard" },
            ].map(({ label, href }) => (
              <a
                key={href}
                href={href}
                className={`block py-1 px-2 rounded hover:bg-gray-100 transition ${
                  sector && href.includes(sector)
                    ? "font-semibold text-black"
                    : "text-gray-600"
                }`}
              >
                {label}
              </a>
            ))}
          </div>
        </div>

        {/* Färg */}
        {allColors.length > 0 && (
          <div>
            <div className="flex items-center justify-between mb-2">
              <h3 className="font-semibold text-gray-800">Färg</h3>
              {selectedColor && (
                <button
                  onClick={() => setSelectedColor(null)}
                  className="text-xs text-gray-400 hover:text-gray-600"
                >
                  Rensa
                </button>
              )}
            </div>
            <div className="flex flex-wrap gap-3">
              {allColors.slice(0, 12).map((color) => {
                const clean = cleanColorName(color)
                const hex = COLOR_MAP[clean] || "#ccc"
                return (
                  <button
                    key={color}
                    onClick={() =>
                      setSelectedColor(selectedColor === color ? null : color)
                    }
                    className={`w-6 h-6 rounded-full border border-gray-300 transition ${
                      selectedColor === color
                        ? "ring-2 ring-offset-1 ring-black"
                        : "hover:scale-110"
                    }`}
                    style={{ backgroundColor: hex }}
                    title={clean}
                  />
                )
              })}
            </div>
          </div>
        )}

        {/* Storlek */}
        {allSizes.length > 0 && (
          <div>
            <div className="flex items-center justify-between mb-2">
              <h3 className="font-semibold text-gray-800">Storlek</h3>
              {selectedSize && (
                <button
                  onClick={() => setSelectedSize(null)}
                  className="text-xs text-gray-400 hover:text-gray-600"
                >
                  Rensa
                </button>
              )}
            </div>
            <div className="flex flex-wrap gap-2">
              {allSizes.slice(0, 12).map((size) => (
                <button
                  key={size}
                  onClick={() =>
                    setSelectedSize(selectedSize === size ? null : size)
                  }
                  className={`text-xs border px-2 py-1 rounded transition ${
                    selectedSize === size
                      ? "bg-black text-white border-black"
                      : "text-gray-600 border-gray-300 hover:border-gray-500"
                  }`}
                >
                  {size}
                </button>
              ))}
            </div>
          </div>
        )}
      </aside>

      {/* Product grid */}
      <div>
        {(selectedColor || selectedSize) && (
          <p className="text-xs text-gray-500 mb-4">
            {filteredProducts.length} produkt
            {filteredProducts.length !== 1 ? "er" : ""} visas
            {selectedColor ? ` · Färg: ${cleanColorName(selectedColor)}` : ""}
            {selectedSize ? ` · Storlek: ${selectedSize}` : ""}
          </p>
        )}

        {filteredProducts.length === 0 ? (
          <p className="text-sm text-gray-500 py-8">Inga produkter hittades.</p>
        ) : (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            {filteredProducts.map((p, index) => {
              const itemNo = getItemNo(p)
              if (!itemNo) return null
              return (
                <ProductCard
                  key={itemNo}
                  product={p}
                  isTopMatch={!!query && index < 4}
                />
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}

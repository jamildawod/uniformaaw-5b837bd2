import { ProductCard } from "@/components/ProductCard"
import { fetchProducts } from "@/lib/api"
import { filterHomepageProducts, getItemNo } from "@/lib/product-utils"

async function fetchPreviewProducts() {
  return fetchProducts({ limit: 32 })
}

export async function CategoryGrid() {
  const allProducts = await fetchPreviewProducts()
  const products = filterHomepageProducts(allProducts as any[])

  return (
    <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
      <div className="mb-8">
        <p className="text-xs uppercase tracking-widest text-gray-400 mb-2 font-medium">
          Alla branscher
        </p>
        <h2 className="text-2xl md:text-3xl font-bold text-gray-900">
          Utforska alla kategorier
        </h2>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
        {products.slice(0, 32).map((p: any) => {
          const itemNo = getItemNo(p)
          if (!itemNo) return null
          return <ProductCard key={itemNo} product={p} />
        })}
      </div>

      <div className="flex justify-center mt-10">
        <a
          href="/shop"
          className="px-6 py-3 rounded-xl bg-black text-white text-sm font-semibold hover:opacity-90 transition"
        >
          Visa fler produkter
        </a>
      </div>
    </section>
  )
}

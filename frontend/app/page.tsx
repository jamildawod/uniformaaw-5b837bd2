import { IndustrySection } from "@/components/home/IndustrySection"
import ContactBlock from "@/components/home/ContactBlock"
import { ProductCard } from "@/components/ProductCard"
import { fetchProductOverrides } from "@/lib/api"
import { filterHomepageProducts, getItemNo } from "@/lib/product-utils"

async function fetchProducts() {
  const res = await fetch("https://uniforma.livosys.se/api/v1/products?limit=2000", {
    cache: "no-store",
  })
  if (!res.ok) return []

  const data = await res.json()
  return Array.isArray(data) ? data : []
}

export default async function HomePage() {
  const [products, overrides] = await Promise.all([
    fetchProducts(),
    fetchProductOverrides(),
  ])

  const visibleProducts = filterHomepageProducts(products, overrides)
  const homepageProducts = visibleProducts.slice(0, 40)

  return (
    <>
      <IndustrySection />
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
          {homepageProducts.map((product: any) => (
            <ProductCard
              key={getItemNo(product)}
              product={product}
            />
          ))}
        </div>
      </section>
      <ContactBlock />
    </>
  )
}

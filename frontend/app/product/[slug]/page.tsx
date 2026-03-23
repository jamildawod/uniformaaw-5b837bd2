import { ProductDetailClient } from "@/components/ProductDetailClient"

async function getProduct(slug: string) {
  try {
    const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/products/${slug}`, {
      cache: "no-store",
    })

    if (!res.ok) return null

    const data = await res.json()

    return data ?? null
  } catch (e) {
    console.error("Product fetch failed:", e)
    return null
  }
}

export default async function ProductPage({ params }: { params: { slug: string } }) {
  const product = await getProduct(params.slug)

  const safeProduct = {
    ...product,
    images: product?.images ?? [],
    variants: product?.variants ?? [],
    certifications: product?.certifications ?? [],
    care_instructions: product?.care_instructions ?? [],
    tags: product?.tags ?? [],
  }

  if (!product) {
    return <div>Produkt kunde inte laddas</div>
  }

  return <ProductDetailClient product={safeProduct} />
}

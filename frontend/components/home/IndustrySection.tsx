import Link from "next/link"
import { fetchCategories } from "@/lib/api"

// Static background images keyed by category slug.
const categoryImages: Record<string, string> = {
  dental:          "/2024dentalcontainer.jpg",
  djursjukvard:    "/2024djursjukvardcontainer.jpg",
  kok:             "/kok624x360.jpg",
  "stad-service":  "/namnlos-design-4.webp",
  "skonhet-halsa": "/spawellnessnew2024.jpg",
  "vard-omsorg":   "/vard624x360.jpg",
  default:         "/images/placeholder.webp",
}

// Short descriptors per category slug.
const CATEGORY_CONFIG: Record<string, { description: string }> = {
  dental:          { description: "Tandvård & klinik" },
  djursjukvard:    { description: "Veterinär & djursjukvård" },
  "skonhet-halsa": { description: "Spa, beauty & wellness" },
  "vard-omsorg":   { description: "Hemtjänst & omsorg" },
  kok:             { description: "Restaurang, hotell & kök" },
  "stad-service":  { description: "Facility & lokalvård" },
}

export async function IndustrySection() {
  const categories = await fetchCategories()

  return (
    <section className="space-y-6 max-w-[83rem] mx-auto px-6">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">
            Branscher & arbetsområden
          </p>
          <h2 className="text-2xl font-semibold text-slate-900">
            Hitta produkter för din bransch
          </h2>
        </div>
        <Link
          href="/shop"
          className="text-sm font-medium text-slate-500 hover:text-slate-900"
        >
          Visa alla produkter →
        </Link>
      </div>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
        {categories.map((category) => {
          const bgImage =
            categoryImages[category.slug] || categoryImages.default

          const config = CATEGORY_CONFIG[category.slug]

          return (
            <Link
              key={category.slug}
              href={`/shop?sector=${category.sector_slug ?? category.slug}`}
              className="group relative overflow-hidden rounded-2xl h-[14.5rem]"
              style={{
                backgroundImage: `linear-gradient(rgba(0,0,0,0.4), rgba(0,0,0,0.4)), url(${bgImage})`,
                backgroundSize: "cover",
                backgroundPosition: "center",
              }}
            >

              {/* Content */}
              <div className="absolute bottom-4 left-4 z-10 text-white">
                <p className="text-xs uppercase tracking-wide opacity-80">
                  {config?.description}
                </p>
                <p className="text-lg font-semibold">{category.name}</p>
                <span className="mt-2 inline-block rounded-full border border-white/40 px-3 py-1 text-xs">
                  Utforska →
                </span>
              </div>
            </Link>
          )
        })}
      </div>
    </section>
  )
}

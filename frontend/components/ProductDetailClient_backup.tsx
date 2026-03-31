"use client"

import { useState } from "react"
import { safeArray } from "@/components/SafeArray"
import type { StoreVariant } from "@/components/ProductCard"
import { VariantSelector } from "@/components/VariantSelector"
import { resolveImageUrl } from "@/lib/product-utils"

// ── Care instruction text labels ──────────────────────────────────────────────

const CARE_MAP: Record<string, string> = {
  dry_clean: "Kemtvätt",
  machine_wash: "Maskintvätt",
  machine_wash_85: "Maskintvätt 85°",
  hand_wash: "Handtvätt",
  no_bleach: "Ej blekning",
  bleach: "Blekning",
  tumble_dry: "Torktumlas",
  tumble_dry_low: "Torktumlas låg",
  no_tumble_dry: "Ej torktumling",
  iron_low: "Strykning låg",
  iron_medium: "Strykning medel",
  iron_high: "Strykning hög",
  no_iron: "Ej strykning",
  wash_30: "Tvätt 30°C",
  wash_40: "Tvätt 40°C",
  wash_60: "Tvätt 60°C",
  wash_85: "Tvätt 85°C",
  line_dry: "Hängtorkning",
  flat_dry: "Torkas plant",
  no_wash: "Ej tvätt",
}

// ── Care instruction SVG icons ────────────────────────────────────────────────

function CareIcon({ type }: { type: string }) {
  const key = (typeof type === "string" ? type : String(type)).toLowerCase().trim()
  const label = CARE_MAP[key] ?? key
  const stroke = "#374151"
  const sw = 1.5

  let icon: JSX.Element

  if (key === "no_bleach") {
    icon = (
      <svg width="36" height="36" viewBox="0 0 36 36" fill="none">
        <path d="M18 6L32 30H4L18 6z" stroke={stroke} strokeWidth={sw} strokeLinejoin="round" />
        <path d="M10 26L26 12" stroke={stroke} strokeWidth={sw} strokeLinecap="round" />
      </svg>
    )
  } else if (key === "bleach") {
    icon = (
      <svg width="36" height="36" viewBox="0 0 36 36" fill="none">
        <path d="M18 6L32 30H4L18 6z" stroke={stroke} strokeWidth={sw} strokeLinejoin="round" />
      </svg>
    )
  } else if (key === "tumble_dry") {
    icon = (
      <svg width="36" height="36" viewBox="0 0 36 36" fill="none">
        <rect x="5" y="5" width="26" height="26" rx="3" stroke={stroke} strokeWidth={sw} />
        <circle cx="18" cy="18" r="7" stroke={stroke} strokeWidth={sw} />
      </svg>
    )
  } else if (key === "tumble_dry_low") {
    icon = (
      <svg width="36" height="36" viewBox="0 0 36 36" fill="none">
        <rect x="5" y="5" width="26" height="26" rx="3" stroke={stroke} strokeWidth={sw} />
        <circle cx="18" cy="18" r="7" stroke={stroke} strokeWidth={sw} />
        <circle cx="25" cy="11" r="1.8" fill={stroke} />
      </svg>
    )
  } else if (key === "no_tumble_dry") {
    icon = (
      <svg width="36" height="36" viewBox="0 0 36 36" fill="none">
        <rect x="5" y="5" width="26" height="26" rx="3" stroke={stroke} strokeWidth={sw} />
        <circle cx="18" cy="18" r="7" stroke={stroke} strokeWidth={sw} />
        <path d="M13 13l10 10M23 13L13 23" stroke={stroke} strokeWidth={sw} strokeLinecap="round" />
      </svg>
    )
  } else if (key === "line_dry") {
    icon = (
      <svg width="36" height="36" viewBox="0 0 36 36" fill="none">
        <rect x="5" y="5" width="26" height="26" rx="3" stroke={stroke} strokeWidth={sw} />
        <line x1="18" y1="9" x2="18" y2="27" stroke={stroke} strokeWidth={sw} strokeLinecap="round" />
      </svg>
    )
  } else if (key === "flat_dry") {
    icon = (
      <svg width="36" height="36" viewBox="0 0 36 36" fill="none">
        <rect x="5" y="5" width="26" height="26" rx="3" stroke={stroke} strokeWidth={sw} />
        <line x1="9" y1="18" x2="27" y2="18" stroke={stroke} strokeWidth={sw} strokeLinecap="round" />
      </svg>
    )
  } else if (key === "iron_low") {
    icon = (
      <svg width="36" height="36" viewBox="0 0 36 36" fill="none">
        <path d="M6 25L9 15Q10 11 15 11H27Q31 11 31 15L29 21Q28 25 24 25Z" stroke={stroke} strokeWidth={sw} strokeLinejoin="round" />
        <line x1="7" y1="25" x2="29" y2="25" stroke={stroke} strokeWidth={sw} strokeLinecap="round" />
        <circle cx="15" cy="18" r="1.8" fill={stroke} />
      </svg>
    )
  } else if (key === "iron_medium") {
    icon = (
      <svg width="36" height="36" viewBox="0 0 36 36" fill="none">
        <path d="M6 25L9 15Q10 11 15 11H27Q31 11 31 15L29 21Q28 25 24 25Z" stroke={stroke} strokeWidth={sw} strokeLinejoin="round" />
        <line x1="7" y1="25" x2="29" y2="25" stroke={stroke} strokeWidth={sw} strokeLinecap="round" />
        <circle cx="13" cy="18" r="1.8" fill={stroke} />
        <circle cx="19" cy="18" r="1.8" fill={stroke} />
      </svg>
    )
  } else if (key === "iron_high") {
    icon = (
      <svg width="36" height="36" viewBox="0 0 36 36" fill="none">
        <path d="M6 25L9 15Q10 11 15 11H27Q31 11 31 15L29 21Q28 25 24 25Z" stroke={stroke} strokeWidth={sw} strokeLinejoin="round" />
        <line x1="7" y1="25" x2="29" y2="25" stroke={stroke} strokeWidth={sw} strokeLinecap="round" />
        <circle cx="12" cy="18" r="1.8" fill={stroke} />
        <circle cx="18" cy="18" r="1.8" fill={stroke} />
        <circle cx="24" cy="18" r="1.8" fill={stroke} />
      </svg>
    )
  } else if (key === "no_iron") {
    icon = (
      <svg width="36" height="36" viewBox="0 0 36 36" fill="none">
        <path d="M6 25L9 15Q10 11 15 11H27Q31 11 31 15L29 21Q28 25 24 25Z" stroke={stroke} strokeWidth={sw} strokeLinejoin="round" />
        <line x1="7" y1="25" x2="29" y2="25" stroke={stroke} strokeWidth={sw} strokeLinecap="round" />
        <path d="M13 14l10 9M23 14L13 23" stroke={stroke} strokeWidth={sw} strokeLinecap="round" />
      </svg>
    )
  } else if (key === "dry_clean") {
    icon = (
      <svg width="36" height="36" viewBox="0 0 36 36" fill="none">
        <circle cx="18" cy="18" r="12" stroke={stroke} strokeWidth={sw} />
        <text x="18" y="23" textAnchor="middle" fontSize="12" fill={stroke} fontFamily="system-ui,sans-serif" fontWeight="700">P</text>
      </svg>
    )
  } else if (key === "hand_wash") {
    icon = (
      <svg width="36" height="36" viewBox="0 0 36 36" fill="none">
        <path d="M6 11h24v13a3 3 0 01-3 3H9a3 3 0 01-3-3V11z" stroke={stroke} strokeWidth={sw} />
        <path d="M4 11h28" stroke={stroke} strokeWidth={sw} strokeLinecap="round" />
        <path d="M14 23v-5m4 5v-7m4 7v-5" stroke={stroke} strokeWidth={sw} strokeLinecap="round" />
        <path d="M12 23q0 1.5 2 1.5h8q2 0 2-1.5" stroke={stroke} strokeWidth={sw} strokeLinecap="round" />
      </svg>
    )
  } else if (key === "no_wash") {
    icon = (
      <svg width="36" height="36" viewBox="0 0 36 36" fill="none">
        <path d="M6 11h24v13a3 3 0 01-3 3H9a3 3 0 01-3-3V11z" stroke={stroke} strokeWidth={sw} />
        <path d="M4 11h28" stroke={stroke} strokeWidth={sw} strokeLinecap="round" />
        <path d="M12 15l12 9M24 15L12 24" stroke={stroke} strokeWidth={sw} strokeLinecap="round" />
      </svg>
    )
  } else {
    // Washtub with optional temperature (machine_wash, wash_30, wash_40, wash_60, wash_85, machine_wash_85)
    const match = key.match(/(\d+)/)
    const temp = match ? match[1] : null
    icon = (
      <svg width="36" height="36" viewBox="0 0 36 36" fill="none">
        <path d="M6 11h24v13a3 3 0 01-3 3H9a3 3 0 01-3-3V11z" stroke={stroke} strokeWidth={sw} />
        <path d="M4 11h28" stroke={stroke} strokeWidth={sw} strokeLinecap="round" />
        {temp ? (
          <text x="18" y="23" textAnchor="middle" fontSize="8" fill={stroke} fontFamily="system-ui,sans-serif" fontWeight="700">{temp}°</text>
        ) : (
          <circle cx="18" cy="19" r="4" stroke={stroke} strokeWidth={sw} />
        )}
      </svg>
    )
  }

  return (
    <div className="flex flex-col items-center gap-1.5" title={label}>
      {icon}
      <span className="text-[10px] text-stone-400 text-center leading-tight" style={{ maxWidth: 52 }}>
        {label}
      </span>
    </div>
  )
}

// ─────────────────────────────────────────────────────────────────────────────

export function ProductDetailClient({ product }: any) {
  const directImages: any[] = safeArray(product?.images)
  const variants = safeArray(product?.variants) as StoreVariant[]

  // Collect all images: direct first, then variant images as fallback gallery
  const variantImages: any[] = variants.flatMap((v) => safeArray(v.images))
  const images: any[] = directImages.length > 0 ? directImages : variantImages
  const certifications: any[] = safeArray(product?.certifications)
  const care: any[] = safeArray(product?.care_instructions)
  const tags: any[] = safeArray(product?.tags)

  console.log("[DEBUG] product.variants:", product?.variants)

  const [selectedSize, setSelectedSize] = useState<string | null>(null)
  const [selectedColor, setSelectedColor] = useState<string | null>(null)
  const [, setSelectedVariant] = useState<StoreVariant | null>(null)
  const [activeImage, setActiveImage] = useState(0)

  const mainImageUrl =
    images.length > 0
      ? resolveImageUrl(images[Math.min(activeImage, images.length - 1)])
      : (product?.primary_image ?? null)

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 py-8 sm:py-12">

      {/* ── TOP GRID: image left | info right ── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 lg:gap-16 items-start">

        {/* LEFT: Image gallery */}
        <div className="space-y-4">
          <div className="aspect-square bg-stone-50 rounded-2xl overflow-hidden border border-stone-100 flex items-center justify-center">
            <img
              src={mainImageUrl ?? "/placeholder.jpg"}
              alt={product?.name ?? "Produktbild"}
              className="w-full h-full object-contain p-8"
            />
          </div>

          {images.length > 1 && (
            <div className="overflow-x-auto flex gap-2">
              {images.map((img: any, i: number) => (
                <button
                  key={i}
                  type="button"
                  onClick={() => setActiveImage(i)}
                  className={`w-16 h-16 rounded-xl border-2 overflow-hidden bg-stone-50 transition flex items-center justify-center ${
                    activeImage === i
                      ? "border-stone-950"
                      : "border-stone-200 hover:border-stone-400"
                  }`}
                >
                  <img src={resolveImageUrl(img)} alt="" className="w-full h-full object-contain p-1" />
                </button>
              ))}
            </div>
          )}
        </div>

        {/* RIGHT: Title + selectors + eco/QR */}
        <div className="space-y-8">

          {/* Header */}
          <div>
            {product?.brand && product.brand !== "Hejco" && (
              <p className="text-xs font-semibold uppercase tracking-widest text-stone-400 mb-1">
                {product.brand}
              </p>
            )}
            <h1 className="text-xl sm:text-2xl lg:text-3xl font-bold text-stone-950 leading-tight">
              {product?.name}
            </h1>
            {product?.category?.name && (
              <p className="mt-1 text-sm text-stone-400">{product.category.name}</p>
            )}
            {(product?.supplier_sku || product?.sku) && (
              <p className="mt-2 text-sm text-stone-400">
                Artikelnummer: {product.supplier_sku || product.sku}
              </p>
            )}
          </div>

          {/* Variant selector */}
          {variants.length > 0 && (
            <VariantSelector
              variants={variants}
              selectedSize={selectedSize}
              selectedColor={selectedColor}
              onSizeChange={setSelectedSize}
              onColorChange={setSelectedColor}
              onVariantChange={setSelectedVariant}
            />
          )}

          {/* Eco certifications + QR inline */}
          {(certifications.length > 0 || product?.qr_code) && (
            <div className="flex items-start gap-6 pt-2">
              {certifications.length > 0 && (
                <div className="flex flex-wrap gap-2">
                  {certifications.map((c: any, i: number) => (
                    <span
                      key={i}
                      className="text-xs font-medium px-3 py-1 rounded-full border border-emerald-200 bg-emerald-50 text-emerald-700"
                    >
                      {c}
                    </span>
                  ))}
                </div>
              )}
              {product?.qr_code && (
                <img
                  src={product.qr_code}
                  alt="QR-kod"
                  className="w-16 h-16 rounded-lg border border-stone-200 flex-shrink-0"
                />
              )}
            </div>
          )}

          {/* Description */}
          {product?.description && (
            <div className="border-t border-stone-100 pt-6">
              <h2 className="text-xs font-semibold uppercase tracking-widest text-stone-400 mb-3">
                Beskrivning
              </h2>
              <p className="text-stone-700 text-sm leading-relaxed">{product.description}</p>
            </div>
          )}

          {/* Material */}
          {product?.material && (
            <div>
              <h2 className="text-xs font-semibold uppercase tracking-widest text-stone-400 mb-2">
                Material
              </h2>
              <p className="text-stone-700 text-sm">{product.material}</p>
            </div>
          )}

          {/* Passform */}
          {product?.fit && (
            <div>
              <h2 className="text-xs font-semibold uppercase tracking-widest text-stone-400 mb-2">
                Passform
              </h2>
              <p className="text-stone-700 text-sm">{product.fit}</p>
            </div>
          )}

          {/* Care instructions */}
          {care.length > 0 && (
            <div>
              <h2 className="text-xs font-semibold uppercase tracking-widest text-stone-400 mb-4">
                Skötselråd
              </h2>
              <div className="flex flex-wrap gap-6">
                {care.map((c: any, i: number) => (
                  <CareIcon key={i} type={c} />
                ))}
              </div>
            </div>
          )}

          {/* Tags */}
          {tags.length > 0 && (
            <div>
              <h2 className="text-xs font-semibold uppercase tracking-widest text-stone-400 mb-3">
                Taggar
              </h2>
              <div className="flex flex-wrap gap-2">
                {tags.map((t: any, i: number) => (
                  <span
                    key={i}
                    className="text-xs px-3 py-1 rounded-full bg-stone-100 text-stone-600"
                  >
                    {t}
                  </span>
                ))}
              </div>
            </div>
          )}

        </div>
      </div>

    </div>
  )
}

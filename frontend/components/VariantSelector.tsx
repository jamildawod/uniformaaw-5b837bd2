"use client"

import { useMemo, useEffect } from "react"
import type { StoreVariant } from "@/components/ProductCard"
import { COLOR_MAP } from "@/components/ProductCard"

// ── Color helpers ───────────────────────────────────────────────────────────

/** Extract readable label from raw PIM value, e.g. "H440:M3-1 Violett" → "Violett" */
function extractColorLabel(raw: string): string {
  const parts = raw.trim().split(/\s+/)
  return parts[parts.length - 1] || raw
}

/** Map extracted label to a hex color, with fallback */
function getColorHex(label: string): string {
  const key = label.toLowerCase()
  if (COLOR_MAP[key]) return COLOR_MAP[key]
  for (const [k, v] of Object.entries(COLOR_MAP)) {
    if (key.includes(k)) return v
  }
  return "#d1d5db"
}

// ── Size normalization (frontend) ──────────────────────────────────────────

const SIZE_ORDER = ["2XS", "XS", "S", "M", "L", "XL", "2XL", "3XL", "4XL", "5XL", "6XL"]

function normalizeSizeFe(value?: string | null): string | null {
  if (!value) return null
  const v = value.trim().toUpperCase()
  if (v === "XXS") return "2XS"
  if (v === "XXL") return "2XL"
  return v
}

function sortSizes(sizes: string[]): string[] {
  return [...sizes].sort((a, b) => {
    const ai = SIZE_ORDER.indexOf(a)
    const bi = SIZE_ORDER.indexOf(b)
    if (ai !== -1 && bi !== -1) return ai - bi
    if (ai !== -1) return -1
    if (bi !== -1) return 1
    return a.localeCompare(b)
  })
}

// ── Props ──────────────────────────────────────────────────────────────────

interface VariantSelectorProps {
  variants: StoreVariant[]
  selectedSize: string | null
  selectedColor: string | null
  onSizeChange: (size: string | null) => void
  onColorChange: (color: string | null) => void
  onVariantChange: (variant: StoreVariant | null) => void
}

// ── Component ──────────────────────────────────────────────────────────────

export function VariantSelector({
  variants,
  selectedSize,
  selectedColor,
  onSizeChange,
  onColorChange,
  onVariantChange,
}: VariantSelectorProps) {
  const activeVariants = variants.filter((v) => v.is_active !== false)

  // All unique colors
  const allColors = useMemo(() => {
    const seen = new Set<string>()
    for (const v of activeVariants) {
      if (v.color?.trim()) seen.add(v.color.trim())
    }
    return Array.from(seen).sort()
  }, [activeVariants])

  // Variants filtered by selected color (or all if no color selected)
  const active = useMemo(() => {
    if (!selectedColor) return activeVariants
    return activeVariants.filter((v) => v.color?.trim() === selectedColor)
  }, [activeVariants, selectedColor])

  // All unique sizes from the currently active (color-filtered) variants
  const allSizes = useMemo(() => {
    const seen = new Set<string>()
    for (const v of active) {
      const raw = v.size?.trim()
      const label = normalizeSizeFe(raw)
      if (raw || label) {
        seen.add(label ?? raw!)
      }
    }

    const result = Array.from(seen)

    // Fallback if no sizes exist
    if (result.length === 0 && active.length > 0) {
      return ["ONE SIZE"]
    }

    return sortSizes(result)
  }, [active])

  // Match a variant to the selected size label
  const matchesSize = (v: StoreVariant, label: string) => {
    if (label === "ONE SIZE") return true

    const raw = v.size?.trim()
    const normalized = normalizeSizeFe(raw)

    return normalized === label || raw === label
  }

  // Resolve selected variant whenever size or color changes
  useEffect(() => {
    if (!selectedSize && !selectedColor) {
      onVariantChange(null)
      return
    }

    const match = active.find((v) => {
      const sizeOk = selectedSize ? matchesSize(v, selectedSize) : true
      return sizeOk
    })

    onVariantChange(match ?? null)
  }, [selectedSize, selectedColor, active])

  // Reset size when color changes and current size is no longer available
  useEffect(() => {
    if (selectedSize && !allSizes.includes(selectedSize)) {
      onSizeChange(null)
    }
  }, [allSizes, selectedSize])

  const hasColors = allColors.length > 0
  const hasSizes = allSizes.length > 0

  return (
    <div className="space-y-5">
      {/* Color selector */}
      {hasColors && (
        <div>
          <p className="text-xs font-semibold uppercase tracking-widest text-stone-400 mb-3">
            Färg{selectedColor ? `: ${extractColorLabel(selectedColor)}` : ""}
          </p>
          <div className="flex flex-wrap gap-4">
            {allColors.map((color) => {
              const label = extractColorLabel(color)
              const hex = getColorHex(label)
              return (
                <button
                  key={color}
                  type="button"
                  onClick={() => onColorChange(selectedColor === color ? null : color)}
                  title={label}
                  className="flex flex-col items-center gap-1.5"
                >
                  <span
                    className={`w-8 h-8 rounded-full border-2 transition-all block ${
                      selectedColor === color
                        ? "border-stone-950 ring-2 ring-offset-2 ring-stone-800"
                        : "border-stone-200 hover:border-stone-500"
                    }`}
                    style={{ backgroundColor: hex }}
                  />
                  <span className="text-[10px] text-stone-500 leading-tight text-center" style={{ maxWidth: 48 }}>
                    {label}
                  </span>
                </button>
              )
            })}
          </div>
        </div>
      )}

      {/* Size selector */}
      {hasSizes && (
        <div>
          <p className="text-xs font-semibold uppercase tracking-widest text-stone-400 mb-2">
            Storlek{selectedSize ? `: ${selectedSize}` : ""}
          </p>
          <div className="flex flex-wrap gap-2">
            {allSizes.map((size) => (
              <button
                key={size}
                type="button"
                onClick={() => onSizeChange(selectedSize === size ? null : size)}
                className={`min-w-[2.75rem] px-3 py-1.5 rounded-lg border text-sm font-medium transition ${
                  selectedSize === size
                    ? "border-stone-950 bg-stone-950 text-white"
                    : "border-stone-200 text-stone-700 hover:border-stone-400"
                }`}
              >
                {size}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

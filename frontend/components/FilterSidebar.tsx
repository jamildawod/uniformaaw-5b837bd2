"use client";

import { startTransition } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { SlidersHorizontal, X } from "lucide-react";
import { FilterSection } from "@/components/FilterSection";
import { normalizeSize } from "@/lib/size-filter";

type FilterOption = {
  slug: string;
  name: string;
};

type FilterSidebarProps = {
  categories: FilterOption[];
  uniqueSizes: string[];
  colors: string[];
  selectedCategory: string;
  selectedSector?: string;
  selectedSize: string;
  selectedColor: string;
};

export function FilterSidebar({
  categories,
  uniqueSizes = [],
  colors = [],
  selectedCategory,
  selectedSector = "",
  selectedSize,
  selectedColor,
}: FilterSidebarProps) {
  const pathname = usePathname();
  const router = useRouter();
  const searchParams = useSearchParams();
  const normalizedSelectedSize = normalizeSize(selectedSize) ?? "";

  const activeFilters: Array<{ label: string; key: string }> = [];

  if (selectedCategory) {
    const category = (categories ?? []).find((item) => item.slug === selectedCategory);
    activeFilters.push({
      label: category?.name ?? selectedCategory,
      key: "category",
    });
  }

  if (selectedSector) {
    activeFilters.push({ label: selectedSector, key: "sector" });
  }

  if (normalizedSelectedSize) {
    activeFilters.push({ label: normalizedSelectedSize, key: "size" });
  }

  if (selectedColor) {
    activeFilters.push({ label: selectedColor, key: "color" });
  }

  const updateFilter = (key: string, value: string | null) => {
    const nextParams = new URLSearchParams(searchParams.toString());
    nextParams.delete("page");
    const normalizedValue =
      key === "size" ? normalizeSize(value) ?? "" : value ?? "";

    if (normalizedValue) {
      nextParams.set(key, normalizedValue);
    } else {
      nextParams.delete(key);
    }

    startTransition(() => {
      const query = nextParams.toString();
      router.push(query ? `${pathname}?${query}` : pathname);
    });
  };

  const clearAll = () => {
    startTransition(() => {
      router.push(pathname);
    });
  };

  return (
    <aside className="h-fit lg:sticky lg:top-[100px]">
      <div className="overflow-hidden rounded-3xl border border-stone-200 bg-stone-50 shadow-sm">
        <div className="flex items-center justify-between gap-3 border-b border-stone-200 bg-stone-50/95 px-5 py-4 backdrop-blur">
          <div className="flex items-center gap-2 text-stone-950">
            <SlidersHorizontal className="h-4 w-4" />
            <span className="text-sm font-bold">Filter</span>
            {(activeFilters || []).length > 0 && (
              <span className="inline-flex h-5 min-w-[1.25rem] items-center justify-center rounded-full bg-stone-900 px-1.5 text-[10px] font-bold text-white">
                {(activeFilters || []).length}
              </span>
            )}
          </div>

          {(activeFilters || []).length > 0 && (
            <button
              type="button"
              onClick={clearAll}
              className="inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-medium text-stone-500 transition hover:bg-white hover:text-stone-950"
            >
              <X className="h-3 w-3" />
              Rensa
            </button>
          )}
        </div>

        {(activeFilters || []).length > 0 && (
          <div className="flex flex-wrap gap-2 border-b border-stone-200 px-5 py-4">
            {(activeFilters || []).map((filter) => (
              <button
                key={filter.key}
                type="button"
                onClick={() => updateFilter(filter.key, "")}
                className="inline-flex items-center gap-1.5 rounded-full border border-stone-200 bg-white px-3 py-1.5 text-xs font-medium text-stone-700 transition hover:border-stone-300 hover:bg-stone-100 hover:text-stone-950"
              >
                {filter.label}
                <X className="h-3 w-3" />
              </button>
            ))}
          </div>
        )}

        <div className="max-h-[70vh] space-y-4 overflow-y-auto p-4">
          <FilterSection
            title="Kategorier"
            options={(categories ?? []).map((category) => ({
              label: category.name,
              value: category.slug,
            }))}
            selectedValue={selectedCategory}
            onSelect={(value) => updateFilter("category", value)}
            defaultOpen={true}
            emptyLabel="Alla kategorier"
            initialVisibleCount={10}
          />

          <FilterSection
            title="Storlekar"
            options={(uniqueSizes ?? []).map((size) => ({
              label: size,
              value: size,
            }))}
            selectedValue={normalizedSelectedSize}
            onSelect={(value) => updateFilter("size", normalizeSize(value))}
            defaultOpen={false}
            emptyLabel="Alla storlekar"
          />

          <FilterSection
            title="Färger"
            options={(colors ?? []).map((color) => ({
              label: color,
              value: color,
            }))}
            selectedValue={selectedColor}
            onSelect={(value) => updateFilter("color", value)}
            defaultOpen={false}
            emptyLabel="Alla färger"
          />
        </div>
      </div>
    </aside>
  );
}

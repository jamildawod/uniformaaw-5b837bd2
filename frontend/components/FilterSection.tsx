"use client";

import { useState } from "react";
import { ChevronDown } from "lucide-react";
import { FilterItem } from "@/components/FilterItem";

type FilterOption = {
  label: string;
  value: string;
};

type FilterSectionProps = {
  title: string;
  options: FilterOption[];
  selectedValue: string;
  onSelect: (value: string) => void;
  defaultOpen?: boolean;
  emptyLabel?: string;
  initialVisibleCount?: number;
};

export function FilterSection({
  title,
  options = [],
  selectedValue,
  onSelect,
  defaultOpen = false,
  emptyLabel = "Alla",
  initialVisibleCount,
}: FilterSectionProps) {
  const [open, setOpen] = useState(defaultOpen);
  const [expanded, setExpanded] = useState(false);

  // Guard against undefined being passed at runtime (prop type says string but
  // bad API data or refactoring can produce undefined in JS at runtime).
  const safeSelectedValue = selectedValue ?? "";
  const hasSelection = (safeSelectedValue || []).length > 0;
  const safeOptions = options ?? [];
  const canExpand =
    typeof initialVisibleCount === "number" &&
    (safeOptions || []).length > initialVisibleCount;
  const visibleOptions =
    canExpand && !expanded
      ? safeOptions.slice(0, initialVisibleCount)
      : safeOptions;

  return (
    <section className="rounded-2xl border border-stone-200/80 bg-white/80">
      <button
        type="button"
        onClick={() => setOpen((value) => !value)}
        className="flex w-full items-center justify-between gap-3 px-4 py-3.5 text-left"
      >
        <div className="flex min-w-0 items-center gap-2">
          <h3 className="text-sm font-semibold text-stone-900">{title}</h3>
          {hasSelection && (
            <span className="inline-flex min-w-[1.25rem] items-center justify-center rounded-full bg-stone-900 px-1.5 py-0.5 text-[10px] font-bold text-white">
              1
            </span>
          )}
        </div>
        <ChevronDown
          className={`h-4 w-4 flex-shrink-0 text-stone-400 transition-transform duration-200 ${
            open ? "rotate-180" : ""
          }`}
        />
      </button>

      {open && (
        <div className="space-y-2 border-t border-stone-100 px-4 py-4">
          <FilterItem
            label={emptyLabel}
            selected={!safeSelectedValue}
            onClick={() => onSelect("")}
          />

          {(visibleOptions || []).map((option) => (
            <FilterItem
              key={option.value}
              label={option.label}
              selected={safeSelectedValue === option.value}
              onClick={() =>
                onSelect(safeSelectedValue === option.value ? "" : option.value)
              }
            />
          ))}

          {canExpand && (
            <button
              type="button"
              onClick={() => setExpanded((value) => !value)}
              className="pt-1 text-sm font-medium text-stone-600 transition hover:text-stone-950"
            >
              {expanded
                ? "Visa färre"
                : `Visa fler (${(safeOptions || []).length - initialVisibleCount!})`}
            </button>
          )}
        </div>
      )}
    </section>
  );
}

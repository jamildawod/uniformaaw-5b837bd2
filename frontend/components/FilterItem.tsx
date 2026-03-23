"use client";

import { Check } from "lucide-react";

type FilterItemProps = {
  label: string;
  selected: boolean;
  onClick: () => void;
};

export function FilterItem({ label, selected, onClick }: FilterItemProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-pressed={selected}
      className={`flex w-full items-center gap-3 rounded-xl border px-3 py-2.5 text-left text-sm transition ${
        selected
          ? "border-stone-900 bg-stone-900 text-white shadow-sm"
          : "border-stone-200 bg-white text-stone-700 hover:border-stone-300 hover:bg-stone-50"
      }`}
    >
      <span
        className={`flex h-4 w-4 flex-shrink-0 items-center justify-center rounded border transition ${
          selected
            ? "border-white/70 bg-white/15 text-white"
            : "border-stone-300 bg-stone-50 text-transparent"
        }`}
      >
        <Check className="h-3 w-3" />
      </span>
      <span className="min-w-0 flex-1 truncate font-medium">{label}</span>
    </button>
  );
}

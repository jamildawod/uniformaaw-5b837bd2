"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";

type Category = {
  id: number;
  name: string;
  slug?: string | null;
};

// Static fallback — the 6 main sector categories
// Slugs must match SECTOR_NAMES keys in app/shop/page.tsx
const STATIC_CATEGORIES: Category[] = [
  { id: 4,  name: "Dental",          slug: "dental" },
  { id: 10, name: "Djursjukvård",    slug: "djursjukvard" },
  { id: 34, name: "Skönhet & Hälsa", slug: "beauty" },
  { id: 16, name: "Vård & Omsorg",   slug: "vard" },
  { id: 22, name: "Städ & Service",  slug: "stad" },
  { id: 28, name: "Kök",             slug: "kok" },
];

export default function MegaMenu({
  categories = [],
}: {
  categories?: Category[];
}) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  // Close on outside click
  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    if (open) document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, [open]);

  const items = (categories || []).length > 0 ? categories : STATIC_CATEGORIES;

  return (
    <div className="relative flex-shrink-0" ref={ref}>
      {/* TRIGGER BUTTON */}
      <button
        onClick={() => setOpen(!open)}
        aria-expanded={open}
        className="flex items-center gap-2 rounded-full bg-blue-600 px-5 py-2 text-sm font-semibold text-white transition hover:bg-blue-700"
      >
        <span className="text-base leading-none">☰</span>
        Alla produkter
      </button>

      {/* DROPDOWN */}
      {open && (
        <div className="absolute left-0 top-full z-50 mt-2 w-[min(640px,calc(100vw-2rem))] rounded-2xl border border-slate-200 bg-white p-5 shadow-xl">
          <p className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-3">
            Produktkategorier
          </p>
          <div className="grid grid-cols-3 gap-3">
            {(items || []).map((cat) => (
              <Link
                key={cat.id}
                href={`/shop?sector=${encodeURIComponent(cat.slug ?? cat.name)}`}
                onClick={() => setOpen(false)}
                className="px-4 py-2 rounded-xl border border-slate-200 bg-white text-sm font-medium text-slate-700 transition hover:border-slate-300 hover:bg-slate-50 hover:text-slate-900"
              >
                {cat.name}
              </Link>
            ))}
          </div>
          <div className="mt-4 border-t border-stone-100 pt-4">
            <Link
              href="/shop"
              onClick={() => setOpen(false)}
              className="text-sm font-medium text-blue-600 hover:text-blue-700 mt-3 inline-block"
            >
              Visa alla produkter →
            </Link>
          </div>
        </div>
      )}
    </div>
  );
}

"use client";

import Link from "next/link";
import MegaMenu from "@/components/navigation/MegaMenu";

export function Header() {
  return (
    <header className="bg-white shadow-sm">
      {/* TOP BAR — Logo + Search + Contact */}
      <div className="border-b border-stone-200">
        <div className="mx-auto flex max-w-6xl items-center gap-6 px-6 py-4">
          <Link href="/" className="flex-shrink-0">
            <img
              src="/UNIFORMA_LIGGANDE_SVART.png"
              alt="Uniforma"
              className="h-12 md:h-14 w-auto object-contain"
            />
          </Link>

          <form className="flex w-full flex-1 items-center rounded-full border border-stone-200 bg-stone-50 px-5 py-2.5 transition focus-within:border-stone-400">
            <label htmlFor="uniforma-search" className="sr-only">
              Sök produkter
            </label>
            <input
              id="uniforma-search"
              name="q"
              type="search"
              placeholder="Sök produkter, kategorier eller varumärken..."
              className="w-full border-none bg-transparent text-sm font-medium text-stone-800 placeholder:text-stone-400 focus:outline-none"
            />
          </form>

          <a
            href="/kontakt"
            className="flex-shrink-0 rounded-full border border-stone-900 bg-stone-900 px-6 py-2.5 text-sm font-semibold uppercase tracking-wide text-white transition hover:bg-stone-700"
          >
            Kontakt
          </a>
        </div>
      </div>

      {/* CATEGORY STRIP */}
      <MegaMenu />
    </header>
  );
}

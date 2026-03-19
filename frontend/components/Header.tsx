"use client";

import Link from "next/link";
import MegaMenu from "@/components/navigation/MegaMenu";

const NAV_LINKS = [
  { href: "/",               label: "Startsida" },
  { href: "/om-oss",         label: "Om oss" },
  { href: "/superdeal",      label: "Superdeal" },
  { href: "/storleksguide",  label: "Storleksguide" },
];

export function Header() {
  return (
    <header className="border-b border-stone-200 bg-white shadow-sm">
      {/* TOP BAR — Logo + Search + Contact */}
      <div className="mx-auto flex max-w-7xl items-center gap-6 px-6 py-5 md:px-8">
        <Link href="/" className="flex-shrink-0">
          <img
            src="/UNIFORMA_LIGGANDE_SVART.png"
            alt="Uniforma"
            className="h-16 md:h-20 lg:h-24 w-auto object-contain"
          />
        </Link>

        <form className="flex w-full flex-1 items-center rounded-full border border-stone-300 bg-stone-50 px-6 py-3 shadow-sm transition focus-within:border-stone-500 focus-within:shadow-md">
          <label htmlFor="uniforma-search" className="sr-only">
            Sök produkter
          </label>
          <input
            id="uniforma-search"
            name="q"
            type="search"
            placeholder="Sök produkter, kategorier eller varumärken..."
            className="w-full border-none bg-transparent text-base font-medium text-stone-800 placeholder:text-stone-400 focus:outline-none"
          />
        </form>

        <a
          href="/kontakt"
          className="flex-shrink-0 rounded-full border border-stone-900 bg-stone-900 px-7 py-3 text-sm font-semibold uppercase tracking-widest text-white transition hover:bg-stone-700"
        >
          Kontakt
        </a>
      </div>

      {/* NAV STRIP — Bizay style */}
      <div className="w-full border-t border-b border-gray-200 bg-[#f7f7f7]">
        <div className="mx-auto flex max-w-7xl items-center px-6 md:px-8">
          {/* Alla produkter button */}
          <div className="mr-4 flex h-[50px] flex-shrink-0 items-center border-r border-gray-200 pr-4">
            <MegaMenu />
          </div>

          {/* Nav links with separators */}
          <nav className="flex items-center">
            {NAV_LINKS.map((link, index) => (
              <div key={link.href} className="flex items-center">
                <a
                  href={link.href}
                  className="flex h-[50px] items-center px-5 text-[15px] font-normal tracking-wide text-gray-700 transition hover:text-black"
                >
                  {link.label}
                </a>
                {index !== NAV_LINKS.length - 1 && (
                  <span className="h-5 w-px bg-gray-300" />
                )}
              </div>
            ))}
          </nav>
        </div>
      </div>
    </header>
  );
}

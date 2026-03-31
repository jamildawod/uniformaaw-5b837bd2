"use client";

import { useState } from "react";
import Link from "next/link";
import MegaMenu from "@/components/navigation/MegaMenu";
import SearchAutocomplete from "@/components/search/SearchAutocomplete";

const PRIMARY_NAV_LINKS = [
  { href: "/",               label: "Startsida" },
  { href: "/storleksguide",  label: "Storleksguide" },
  { href: "/superdeal",      label: "Superdeal" },
  { href: "/om-oss",         label: "Om oss" },
];

export function Header() {
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <header className="sticky top-0 z-50 border-b border-stone-200 bg-white shadow-sm">
      {/* TOP BAR — Logo + Search + Contact/Hamburger */}
      <div className="mx-auto flex max-w-7xl items-center gap-3 px-4 py-3 sm:gap-6 sm:px-6 sm:py-5 md:px-8">
        <Link href="/" className="flex-shrink-0">
          <img
            src="/UNIFORMA_LIGGANDE_SVART.png"
            alt="Uniforma"
            className="h-10 w-auto object-contain sm:h-16 md:h-20 lg:h-24"
          />
        </Link>

        <div className="relative w-full flex-1">
          <SearchAutocomplete onNavigate={() => setMobileOpen(false)} />
        </div>

        {/* Desktop contact button */}
        <a
          href="/kontakt"
          className="hidden flex-shrink-0 rounded-full border border-stone-900 bg-stone-900 px-5 py-2.5 text-sm font-semibold uppercase tracking-widest text-white transition hover:bg-stone-700 sm:inline-flex sm:px-7 sm:py-3"
        >
          Kontakt
        </a>

        {/* Mobile hamburger */}
        <button
          type="button"
          onClick={() => setMobileOpen(!mobileOpen)}
          className="flex-shrink-0 rounded-lg p-2 text-stone-700 transition hover:bg-stone-100 md:hidden"
          aria-label="Öppna meny"
          aria-expanded={mobileOpen}
        >
          {mobileOpen ? (
            <svg width="22" height="22" viewBox="0 0 22 22" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
              <path d="M4 4l14 14M18 4L4 18" />
            </svg>
          ) : (
            <svg width="22" height="22" viewBox="0 0 22 22" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
              <path d="M3 6h16M3 11h16M3 16h16" />
            </svg>
          )}
        </button>
      </div>

      {/* NAV STRIP — desktop only */}
      <div className="hidden w-full border-t border-b border-gray-200 bg-[#f7f7f7] md:block">
        <div className="mx-auto flex max-w-7xl items-center px-6 md:px-8">
          {/* Alla produkter button */}
          <div className="mr-4 flex h-[50px] flex-shrink-0 items-center border-r border-gray-200 pr-4">
            <MegaMenu />
          </div>

          {/* Nav links with separators */}
          <nav className="flex min-w-0 flex-1 items-center">
            {PRIMARY_NAV_LINKS.map((link, index) => (
              <div key={link.href} className="flex items-center">
                <a
                  href={link.href}
                  className="flex h-[50px] items-center px-5 text-[15px] font-normal tracking-wide text-gray-700 transition hover:text-black"
                >
                  {link.label}
                </a>
                {index !== PRIMARY_NAV_LINKS.length - 1 && (
                  <span className="h-5 w-px bg-gray-300" />
                )}
              </div>
            ))}
          </nav>
        </div>
      </div>

      {/* MOBILE MENU — slides down when hamburger is open */}
      {mobileOpen && (
        <div className="border-t border-stone-200 bg-white px-4 py-4 md:hidden">
          <nav className="flex flex-col gap-1">
            {PRIMARY_NAV_LINKS.map((link) => (
              <a
                key={link.href}
                href={link.href}
                onClick={() => setMobileOpen(false)}
                className="rounded-lg px-4 py-3 text-base font-medium text-stone-700 transition hover:bg-stone-50 hover:text-stone-950"
              >
                {link.label}
              </a>
            ))}
            <div className="mt-2 border-t border-stone-100 pt-3">
              <MegaMenu />
            </div>
            <a
              href="/kontakt"
              className="mt-3 rounded-full border border-stone-900 bg-stone-900 px-5 py-3 text-center text-sm font-semibold uppercase tracking-widest text-white transition hover:bg-stone-700"
            >
              Kontakt
            </a>
          </nav>
        </div>
      )}
    </header>
  );
}

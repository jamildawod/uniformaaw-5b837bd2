"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

interface NavLinkProps {
  href: string;
  label: string;
  exact?: boolean;
}

export function NavLink({ href, label, exact = false }: NavLinkProps) {
  const pathname = usePathname();
  const isActive = exact ? pathname === href : pathname === href || pathname.startsWith(`${href}/`);

  return (
    <Link
      className={`rounded-2xl px-4 py-3 text-sm font-medium transition-colors ${
        isActive
          ? "bg-ink text-white"
          : "text-slate-700 hover:bg-slate-100 hover:text-ink"
      }`}
      href={href}
    >
      {label}
    </Link>
  );
}

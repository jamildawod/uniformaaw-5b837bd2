import Link from "next/link";

const navItems = [
  { label: "Startsida", href: "/" },
  { label: "Om oss", href: "/om-oss" },
  { label: "Superdeal", href: "/superdeal" },
  { label: "Storleksguide", href: "/storleksguide" },
];

export function Navbar() {
  return (
    <div className="border-b border-stone-100 bg-white">
      <nav className="mx-auto grid max-w-6xl grid-cols-4 px-4 text-center text-sm font-semibold uppercase tracking-[0.3em] text-stone-500">
        {(navItems || []).map((item) => (
          <Link
            key={item.label}
            href={item.href}
            className="flex items-center justify-center border-b-4 border-transparent py-5 transition hover:border-stone-900 hover:text-stone-900"
          >
            {item.label}
          </Link>
        ))}
      </nav>
    </div>
  );
}

import { Tag } from "lucide-react";
import { ProductCard, type StoreProduct } from "@/components/ProductCard";
import { API_URL } from "@/lib/api";

async function getFeaturedProducts(): Promise<StoreProduct[]> {
  try {
    const res = await fetch(`${API_URL}/products?limit=48`, {
      next: { revalidate: 120 },
    });
    if (!res.ok) return [];
    const data = await res.json();
    return Array.isArray(data) ? data : Array.isArray(data?.data) ? data.data : [];
  } catch {
    return [];
  }
}

export const metadata = {
  title: "Superdeal – Uniforma",
  description: "Uniformas bästa erbjudanden på arbetskläder för professionella miljöer.",
};

export default async function SuperdealPage() {
  const products = await getFeaturedProducts();

  return (
    <div className="min-h-screen bg-stone-50 text-stone-950">

      {/* Hero banner */}
      <div className="border-b border-stone-200 bg-stone-950 text-white">
        <div className="mx-auto max-w-[1440px] px-6 py-12 lg:px-10 xl:px-12">
          <div className="flex items-center gap-3">
            <Tag className="h-5 w-5 text-stone-400" />
            <p className="text-xs font-semibold uppercase tracking-widest text-stone-400">
              Erbjudanden
            </p>
          </div>
          <h1 className="mt-2 text-4xl font-bold tracking-tight sm:text-5xl">
            Superdeal
          </h1>
          <p className="mt-4 max-w-xl text-base text-stone-400">
            Våra bästa erbjudanden på professionella arbetskläder. Beställ idag
            och få snabb leverans till din verksamhet.
          </p>
          <a
            href="/kontakt"
            className="mt-6 inline-flex items-center justify-center rounded-full bg-white px-8 py-3 text-sm font-semibold text-stone-950 transition hover:bg-stone-100"
          >
            Be om offert
          </a>
        </div>
      </div>

      {/* Info strip */}
      <div className="border-b border-stone-200 bg-white">
        <div className="mx-auto max-w-[1440px] px-6 py-4 lg:px-10 xl:px-12">
          <div className="flex flex-wrap gap-6 text-sm text-stone-600">
            <span className="flex items-center gap-2">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
              Volymrabatt vid större beställningar
            </span>
            <span className="flex items-center gap-2">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
              Profilering ingår vid sambeställning
            </span>
            <span className="flex items-center gap-2">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
              Offert inom 1–2 arbetsdagar
            </span>
          </div>
        </div>
      </div>

      <main className="mx-auto max-w-[1440px] px-6 py-10 lg:px-10 xl:px-12">

        {products.length > 0 ? (
          <>
            <div className="mb-6 flex items-center justify-between">
              <p className="text-sm text-stone-500">
                <span className="font-semibold text-stone-950">{products.length}</span>{" "}
                {products.length === 1 ? "produkt" : "produkter"}
              </p>
              <a
                href="/shop"
                className="text-sm font-medium text-stone-500 transition hover:text-stone-950"
              >
                Visa hela katalogen →
              </a>
            </div>
            <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6">
              {products.map((product) => (
                <ProductCard key={product.id} product={product} />
              ))}
            </div>
          </>
        ) : (
          <div className="flex flex-col items-center justify-center rounded-2xl border border-dashed border-stone-300 bg-white px-8 py-20 text-center">
            <Tag className="mx-auto mb-4 h-10 w-10 text-stone-300" />
            <h2 className="text-lg font-semibold text-stone-950">
              Inga erbjudanden just nu
            </h2>
            <p className="mt-2 text-sm text-stone-500">
              Kontakta oss för att höra om aktuella kampanjer och volympriser.
            </p>
            <a
              href="/kontakt"
              className="mt-6 inline-flex items-center justify-center rounded-full bg-stone-900 px-6 py-2.5 text-sm font-semibold text-white transition hover:bg-stone-700"
            >
              Kontakta oss
            </a>
          </div>
        )}

        {/* CTA bottom */}
        {products.length > 0 && (
          <div className="mt-12 rounded-2xl border border-stone-200 bg-white p-8 text-center shadow-sm">
            <p className="text-sm font-semibold text-stone-950">
              Vill du beställa för din organisation?
            </p>
            <p className="mt-2 text-sm text-stone-500">
              Vi erbjuder volympriser och anpassade lösningar för professionella verksamheter.
            </p>
            <a
              href="/kontakt"
              className="mt-5 inline-flex items-center justify-center rounded-full bg-stone-900 px-8 py-3 text-sm font-semibold text-white transition hover:bg-stone-700"
            >
              Be om offert
            </a>
          </div>
        )}

      </main>
    </div>
  );
}

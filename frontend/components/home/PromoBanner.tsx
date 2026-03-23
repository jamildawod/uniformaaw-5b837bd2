import Link from "next/link";
import { ArrowRight } from "lucide-react";

export function PromoBanner() {
  return (
    <section className="py-2 md:py-4">
      <div className="relative overflow-hidden rounded-3xl border border-stone-200 bg-gradient-to-r from-stone-950 via-stone-900 to-stone-800 px-6 py-8 text-white md:px-8 md:py-10">
        <div className="absolute right-0 top-0 hidden h-full w-[42%] bg-[radial-gradient(circle_at_top_left,_rgba(255,255,255,0.18),_transparent_48%),radial-gradient(circle_at_bottom_right,_rgba(255,255,255,0.12),_transparent_52%)] md:block" />

        <div className="relative z-10 grid items-center gap-8 md:grid-cols-[minmax(0,1.2fr)_minmax(220px,0.8fr)]">
          <div className="max-w-2xl">
            <p className="text-xs font-semibold uppercase tracking-[0.22em] text-white/60">
              Profilprodukter för företag
            </p>
            <h2 className="mt-2 text-2xl font-bold tracking-tight md:text-3xl">
              Upptäck arbetskläder och produkter som lyfter ditt varumärke
            </h2>
            <p className="mt-3 max-w-xl text-sm leading-6 text-white/70 md:text-base">
              Bygg en enhetlig butikskänsla med kläder och profilprodukter som
              är enkla att beställa, jämföra och kombinera.
            </p>
          </div>

          <div className="flex items-center justify-start md:justify-end">
            <Link
              href="/shop"
              className="inline-flex items-center gap-2 rounded-xl bg-white px-5 py-2.5 text-sm font-semibold text-stone-950 transition hover:bg-stone-100"
            >
              Se mer
              <ArrowRight className="h-4 w-4" />
            </Link>
          </div>
        </div>
      </div>
    </section>
  );
}

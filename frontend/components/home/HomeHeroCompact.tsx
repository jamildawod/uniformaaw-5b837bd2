import Link from "next/link";
import { ArrowRight } from "lucide-react";

export function HomeHeroCompact() {
  return (
    <section className="relative overflow-hidden rounded-3xl bg-black">
      <div className="absolute inset-0 bg-gradient-to-r from-black via-black/90 to-stone-800" />

      <div className="relative min-h-[280px] p-8 md:min-h-[320px] md:p-12">
        <div className="relative z-10 max-w-xl text-white">
          <p className="text-xs font-semibold uppercase tracking-[0.24em] text-white/60">
            Uniforma
          </p>
          <h1 className="mt-4 text-3xl font-bold leading-tight md:text-4xl lg:text-5xl">
            Arbetskläder för professionella miljöer
          </h1>
          <p className="mt-4 max-w-lg text-sm leading-6 text-white/70 md:text-base">
            Uniforma erbjuder noggrant utvalda arbetskläder med fokus på
            kvalitet, funktion och ett enhetligt uttryck.
          </p>

          <div className="mt-6 flex flex-col gap-3 sm:flex-row">
            <Link
              href="/shop"
              className="inline-flex items-center justify-center gap-2 rounded-lg bg-white px-5 py-2.5 text-sm font-semibold text-black transition hover:bg-stone-100"
            >
              Se våra produkter
              <ArrowRight className="h-4 w-4" />
            </Link>
            <Link
              href="/kontakt"
              className="inline-flex items-center justify-center rounded-lg border border-white/30 px-5 py-2.5 text-sm font-semibold text-white transition hover:border-white/50 hover:bg-white/5"
            >
              Kontakta oss
            </Link>
          </div>
        </div>
      </div>
    </section>
  );
}

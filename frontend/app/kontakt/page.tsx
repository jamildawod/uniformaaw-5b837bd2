"use client";

import { useState } from "react";

const inputClass =
  "w-full rounded-xl border border-stone-300 bg-stone-50 px-4 py-3 text-sm text-stone-900 placeholder:text-stone-400 focus:border-stone-500 focus:bg-white focus:outline-none";
const labelClass = "mb-1.5 block text-sm font-semibold text-stone-700";

const API_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "https://api.uniforma.livosys.se/api/v1";

export default function KontaktPage() {
  const [submitted, setSubmitted] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    const form = e.currentTarget;
    const data = {
      name: (form.elements.namedItem("namn") as HTMLInputElement).value.trim(),
      company: (form.elements.namedItem("foretag") as HTMLInputElement).value.trim(),
      org_number: (form.elements.namedItem("orgnr") as HTMLInputElement).value.trim(),
      email: (form.elements.namedItem("epost") as HTMLInputElement).value.trim(),
      phone: (form.elements.namedItem("telefon") as HTMLInputElement).value.trim(),
      subject: (form.elements.namedItem("amne") as HTMLSelectElement).value,
      message: (form.elements.namedItem("meddelande") as HTMLTextAreaElement).value.trim(),
    };
    try {
      const res = await fetch(`${API_URL}/inquiries`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        setError(body?.detail ?? "Något gick fel. Försök igen.");
      } else {
        setSubmitted(true);
      }
    } catch {
      setError("Kunde inte skicka förfrågan. Kontrollera din anslutning och försök igen.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-stone-50 text-stone-950">
      <main className="mx-auto max-w-3xl px-6 py-16">

        {/* Hero */}
        <div className="mb-10">
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-stone-400">
            Kom i kontakt
          </p>
          <h1 className="mt-2 text-4xl font-bold leading-tight text-stone-950">
            Kontakta oss
          </h1>
          <p className="mt-4 max-w-xl text-base text-stone-600">
            Har du frågor om våra produkter eller vill du ha en offert? Tveka
            inte att höra av dig till oss.
          </p>
        </div>

        {/* Contact details — visible high on the page */}
        <div className="mb-10 grid gap-4 sm:grid-cols-3">
          <div className="rounded-2xl border border-stone-200 bg-white p-5 shadow-sm">
            <p className="text-xs font-semibold uppercase tracking-widest text-stone-400">
              Företag
            </p>
            <p className="mt-2 text-sm font-semibold text-stone-900">Uniforma</p>
          </div>
          <div className="rounded-2xl border border-stone-200 bg-white p-5 shadow-sm">
            <p className="text-xs font-semibold uppercase tracking-widest text-stone-400">
              E-post
            </p>
            <a
              href="mailto:hej@uniforma.se"
              className="mt-2 block text-sm font-medium text-stone-900 transition hover:text-stone-600"
            >
              hej@uniforma.se
            </a>
          </div>
          <div className="rounded-2xl border border-stone-200 bg-white p-5 shadow-sm">
            <p className="text-xs font-semibold uppercase tracking-widest text-stone-400">
              Telefon
            </p>
            <a
              href="tel:+46703494913"
              className="mt-2 block text-sm font-medium text-stone-900 transition hover:text-stone-600"
            >
              +46 703 494 913
            </a>
          </div>
        </div>

        {/* Form or success */}
        {submitted ? (
          <div className="rounded-2xl border border-green-200 bg-green-50 p-10 text-center shadow-sm">
            <p className="text-2xl font-semibold text-green-800">
              Tack för din förfrågan!
            </p>
            <p className="mt-3 text-stone-600">Vi återkommer till dig inom kort.</p>
          </div>
        ) : (
          <div className="rounded-2xl border border-stone-200 bg-white p-8 shadow-sm">
            {/* Quote info text */}
            <p className="mb-8 text-sm leading-relaxed text-stone-600">
              Vi arbetar med offertförfrågningar för att kunna erbjuda rätt
              lösning och pris utifrån dina behov. Skicka gärna med så mycket
              information som möjligt i din förfrågan.
            </p>

            <form onSubmit={handleSubmit} className="space-y-6">
              {/* Namn + Företag */}
              <div className="grid gap-6 sm:grid-cols-2">
                <div>
                  <label htmlFor="namn" className={labelClass}>
                    Namn <span className="text-red-500">*</span>
                  </label>
                  <input
                    id="namn"
                    name="namn"
                    type="text"
                    required
                    placeholder="Ditt namn"
                    className={inputClass}
                  />
                </div>
                <div>
                  <label htmlFor="foretag" className={labelClass}>
                    Företag <span className="text-red-500">*</span>
                  </label>
                  <input
                    id="foretag"
                    name="foretag"
                    type="text"
                    required
                    placeholder="Företagsnamn"
                    className={inputClass}
                  />
                </div>
              </div>

              {/* Organisationsnummer */}
              <div>
                <label htmlFor="orgnr" className={labelClass}>
                  Organisationsnummer <span className="text-red-500">*</span>
                </label>
                <input
                  id="orgnr"
                  name="orgnr"
                  type="text"
                  required
                  placeholder="556000-0000"
                  className={inputClass}
                />
              </div>

              {/* E-post + Telefon */}
              <div className="grid gap-6 sm:grid-cols-2">
                <div>
                  <label htmlFor="epost" className={labelClass}>
                    E-postadress <span className="text-red-500">*</span>
                  </label>
                  <input
                    id="epost"
                    name="epost"
                    type="email"
                    required
                    placeholder="din@epost.se"
                    className={inputClass}
                  />
                </div>
                <div>
                  <label htmlFor="telefon" className={labelClass}>
                    Telefonnummer <span className="text-red-500">*</span>
                  </label>
                  <input
                    id="telefon"
                    name="telefon"
                    type="tel"
                    required
                    placeholder="+46 70 000 00 00"
                    className={inputClass}
                  />
                </div>
              </div>

              {/* Ämne */}
              <div>
                <label htmlFor="amne" className={labelClass}>
                  Ämne / typ av förfrågan <span className="text-red-500">*</span>
                </label>
                <select
                  id="amne"
                  name="amne"
                  required
                  className={inputClass}
                >
                  <option value="">Välj ämne…</option>
                  <option value="offert">Offert</option>
                  <option value="produktfraga">Produktfråga</option>
                  <option value="ovrigt">Övrigt</option>
                </select>
              </div>

              {/* Meddelande */}
              <div>
                <label htmlFor="meddelande" className={labelClass}>
                  Meddelande <span className="text-red-500">*</span>
                </label>
                <textarea
                  id="meddelande"
                  name="meddelande"
                  required
                  rows={5}
                  placeholder="Berätta om era behov, antal personer, önskade produkter eller övriga frågor…"
                  className="w-full resize-none rounded-xl border border-stone-300 bg-stone-50 px-4 py-3 text-sm text-stone-900 placeholder:text-stone-400 focus:border-stone-500 focus:bg-white focus:outline-none"
                />
              </div>

              {/* Error */}
              {error && (
                <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
                  {error}
                </div>
              )}

              {/* Submit */}
              <div>
                <button
                  type="submit"
                  disabled={loading}
                  className="w-full rounded-full bg-stone-900 px-8 py-4 text-sm font-semibold uppercase tracking-widest text-white transition hover:bg-stone-700 disabled:cursor-not-allowed disabled:opacity-60"
                >
                  {loading ? "Skickar…" : "Skicka förfrågan"}
                </button>
                <p className="mt-3 text-center text-xs text-stone-400">
                  Kontakta oss för offert · Vi svarar normalt inom 1–2 arbetsdagar.
                </p>
              </div>
            </form>
          </div>
        )}

      </main>
    </div>
  );
}

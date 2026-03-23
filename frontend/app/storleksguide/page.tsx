export const metadata = {
  title: "Storleksguide – Uniforma",
  description: "Hitta rätt passform med Uniformas storleksguide och måtttabeller för arbetskläder.",
};

type SizeRow = { size: string; chest: string; waist: string; hips: string; height: string };
type TrouserRow = { size: string; waist: string; hips: string; inseam: string };

const TOPS: SizeRow[] = [
  { size: "XS",  chest: "80–84",  waist: "64–68",  hips: "88–92",  height: "158–162" },
  { size: "S",   chest: "84–88",  waist: "68–72",  hips: "92–96",  height: "162–166" },
  { size: "M",   chest: "88–94",  waist: "72–78",  hips: "96–100", height: "166–170" },
  { size: "L",   chest: "94–100", waist: "78–84",  hips: "100–106",height: "170–174" },
  { size: "XL",  chest: "100–108",waist: "84–92",  hips: "106–114",height: "174–178" },
  { size: "XXL", chest: "108–116",waist: "92–100", hips: "114–122",height: "178–182" },
  { size: "3XL", chest: "116–124",waist: "100–110",hips: "122–130",height: "182–186" },
  { size: "4XL", chest: "124–132",waist: "110–120",hips: "130–138",height: "186–190" },
];

const TROUSERS: TrouserRow[] = [
  { size: "XS",  waist: "64–68",  hips: "88–92",  inseam: "76–78" },
  { size: "S",   waist: "68–72",  hips: "92–96",  inseam: "78–80" },
  { size: "M",   waist: "72–78",  hips: "96–100", inseam: "80–82" },
  { size: "L",   waist: "78–84",  hips: "100–106",inseam: "81–83" },
  { size: "XL",  waist: "84–92",  hips: "106–114",inseam: "82–84" },
  { size: "XXL", waist: "92–100", hips: "114–122",inseam: "83–85" },
  { size: "3XL", waist: "100–110",hips: "122–130",inseam: "83–85" },
  { size: "4XL", waist: "110–120",hips: "130–138",inseam: "83–85" },
];

const th = "px-4 py-3 text-left text-xs font-semibold uppercase tracking-widest text-stone-400";
const td = "px-4 py-3 text-sm text-stone-700";
const tdFirst = "px-4 py-3 text-sm font-semibold text-stone-950";

export default function StorleksguidePage() {
  return (
    <div className="min-h-screen bg-stone-50 text-stone-950">
      <main className="mx-auto max-w-4xl px-6 py-16">

        {/* Hero */}
        <div className="mb-12">
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-stone-400">
            Passform &amp; mått
          </p>
          <h1 className="mt-2 text-4xl font-bold leading-tight text-stone-950">
            Storleksguide
          </h1>
          <p className="mt-4 max-w-xl text-base text-stone-600">
            Hitta rätt passform med vår storleksguide. Mät dig enligt
            anvisningarna nedan och jämför med tabellerna för bästa resultat.
          </p>
        </div>

        {/* How to measure */}
        <section className="mb-12 rounded-2xl border border-stone-200 bg-white p-8 shadow-sm">
          <h2 className="text-lg font-bold text-stone-950">Så mäter du dig</h2>
          <div className="mt-6 grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
            {[
              {
                label: "Bröstvidd",
                desc: "Mät runt den bredaste delen av bröstet, håll måttbandet vågrätt.",
              },
              {
                label: "Midja",
                desc: "Mät runt den smalaste delen av midjan, vanligtvis strax ovanför naveln.",
              },
              {
                label: "Höftvidd",
                desc: "Mät runt den bredaste delen av höfterna och rumpan.",
              },
              {
                label: "Innerbensläng",
                desc: "Mät från grenen längs insidan av benet ner till marken.",
              },
            ].map((item) => (
              <div key={item.label} className="rounded-xl border border-stone-100 bg-stone-50 p-4">
                <p className="text-sm font-semibold text-stone-950">{item.label}</p>
                <p className="mt-1 text-sm text-stone-500">{item.desc}</p>
              </div>
            ))}
          </div>
          <p className="mt-6 text-xs text-stone-400">
            Alla mått anges i centimeter (cm). Mät på underkläder för bästa precision.
          </p>
        </section>

        {/* Tops table */}
        <section className="mb-10">
          <h2 className="mb-4 text-lg font-bold text-stone-950">
            Övre plagg — tunikor, jackor, toppar
          </h2>
          <div className="overflow-hidden rounded-2xl border border-stone-200 bg-white shadow-sm">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="border-b border-stone-100 bg-stone-50">
                  <tr>
                    <th className={th}>Strl</th>
                    <th className={th}>Bröst (cm)</th>
                    <th className={th}>Midja (cm)</th>
                    <th className={th}>Höft (cm)</th>
                    <th className={th}>Längd (cm)</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-stone-100">
                  {TOPS.map((row) => (
                    <tr key={row.size} className="transition hover:bg-stone-50">
                      <td className={tdFirst}>{row.size}</td>
                      <td className={td}>{row.chest}</td>
                      <td className={td}>{row.waist}</td>
                      <td className={td}>{row.hips}</td>
                      <td className={td}>{row.height}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </section>

        {/* Trousers table */}
        <section className="mb-12">
          <h2 className="mb-4 text-lg font-bold text-stone-950">
            Undre plagg — byxor, shorts
          </h2>
          <div className="overflow-hidden rounded-2xl border border-stone-200 bg-white shadow-sm">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="border-b border-stone-100 bg-stone-50">
                  <tr>
                    <th className={th}>Strl</th>
                    <th className={th}>Midja (cm)</th>
                    <th className={th}>Höft (cm)</th>
                    <th className={th}>Innerben (cm)</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-stone-100">
                  {TROUSERS.map((row) => (
                    <tr key={row.size} className="transition hover:bg-stone-50">
                      <td className={tdFirst}>{row.size}</td>
                      <td className={td}>{row.waist}</td>
                      <td className={td}>{row.hips}</td>
                      <td className={td}>{row.inseam}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </section>

        {/* Tips */}
        <section className="mb-12 rounded-2xl border border-stone-200 bg-white p-8 shadow-sm">
          <h2 className="mb-4 text-lg font-bold text-stone-950">Tips för bästa passform</h2>
          <ul className="space-y-3 text-sm text-stone-600">
            <li className="flex items-start gap-3">
              <span className="mt-0.5 h-1.5 w-1.5 flex-shrink-0 rounded-full bg-stone-400" />
              Ligger du mellan två storlekar? Välj den större för mer rörelsefrihet.
            </li>
            <li className="flex items-start gap-3">
              <span className="mt-0.5 h-1.5 w-1.5 flex-shrink-0 rounded-full bg-stone-400" />
              Arbetskläder är ofta designade för rörelsefrihet och kan sitta något generösare än vanliga kläder.
            </li>
            <li className="flex items-start gap-3">
              <span className="mt-0.5 h-1.5 w-1.5 flex-shrink-0 rounded-full bg-stone-400" />
              Usäker? Kontakta oss — vi hjälper dig välja rätt storlek och passform för din verksamhet.
            </li>
          </ul>
        </section>

        {/* CTA */}
        <div className="rounded-2xl bg-stone-950 p-8 text-center text-white">
          <p className="text-sm font-semibold uppercase tracking-widest text-stone-400">
            Behöver du hjälp?
          </p>
          <h2 className="mt-2 text-2xl font-bold">Kontakta oss för rådgivning</h2>
          <p className="mt-3 text-sm text-stone-400">
            Vi hjälper din organisation hitta rätt storlek och passform.
          </p>
          <a
            href="/kontakt"
            className="mt-6 inline-flex items-center justify-center rounded-full bg-white px-8 py-3 text-sm font-semibold text-stone-950 transition hover:bg-stone-100"
          >
            Skicka förfrågan
          </a>
        </div>

      </main>
    </div>
  );
}

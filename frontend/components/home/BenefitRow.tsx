import { Package, Shield, Truck } from "lucide-react";

const benefits = [
  {
    icon: Package,
    title: "Stort sortiment",
    body: "Hundratals produkter för olika branscher.",
  },
  {
    icon: Shield,
    title: "Kvalitetsgaranti",
    body: "Noggrant utvalda produkter och leverantörer.",
  },
  {
    icon: Truck,
    title: "Snabb leverans",
    body: "Smidig leverans direkt till arbetsplatsen.",
  },
];

export function BenefitRow() {
  return (
    <section className="rounded-2xl border border-stone-200 bg-white px-4 py-4 shadow-sm">
      <div className="grid gap-4 md:grid-cols-3">
        {(benefits || []).map(({ icon: Icon, title, body }) => (
          <div key={title} className="flex items-start gap-3">
            <div className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-xl bg-stone-100">
              <Icon className="h-5 w-5 text-stone-700" />
            </div>
            <div>
              <p className="text-sm font-semibold text-stone-950">{title}</p>
              <p className="mt-1 text-sm text-stone-500">{body}</p>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}

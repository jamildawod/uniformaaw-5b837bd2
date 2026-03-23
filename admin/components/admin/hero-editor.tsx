"use client";

import { useState } from "react";
import { Save, CheckCircle, AlertCircle } from "lucide-react";
import type { SiteContent } from "@/lib/types/content";
import { apiEndpoints } from "@/lib/api/endpoints";

export function HeroEditor({ initial }: { initial: SiteContent | null }) {
  const defaults: SiteContent = {
    hero_title: "",
    hero_subtitle: "",
    hero_cta_text: "",
    hero_cta_link: "/products",
    footer_text: "",
    contact_email: "",
    contact_phone: "",
    contact_address: "",
    ...initial,
  };

  const [form, setForm] = useState(defaults);
  const [status, setStatus] = useState<"idle" | "saving" | "saved" | "error">("idle");

  const handleChange = (field: keyof SiteContent, value: string) => {
    setForm((prev) => ({ ...prev, [field]: value }));
    if (status === "saved") setStatus("idle");
  };

  const handleSave = async () => {
    setStatus("saving");
    try {
      const res = await fetch(apiEndpoints.adminContent, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(form),
      });
      if (!res.ok) throw new Error();
      setStatus("saved");
      setTimeout(() => setStatus("idle"), 3000);
    } catch {
      setStatus("error");
    }
  };

  const field = (label: string, key: keyof SiteContent, placeholder: string, multiline = false) => (
    <div>
      <label className="block text-sm font-medium text-ink mb-1.5">{label}</label>
      {multiline ? (
        <textarea
          className="w-full rounded-xl border border-slate-200 px-4 py-3 text-sm text-ink placeholder-slate-400 focus:border-ink focus:outline-none focus:ring-1 focus:ring-ink resize-none"
          rows={3}
          placeholder={placeholder}
          value={String(form[key] ?? "")}
          onChange={(e) => handleChange(key, e.target.value)}
        />
      ) : (
        <input
          type="text"
          className="w-full rounded-xl border border-slate-200 px-4 py-3 text-sm text-ink placeholder-slate-400 focus:border-ink focus:outline-none focus:ring-1 focus:ring-ink"
          placeholder={placeholder}
          value={String(form[key] ?? "")}
          onChange={(e) => handleChange(key, e.target.value)}
        />
      )}
    </div>
  );

  return (
    <div className="space-y-5">
      <div className="border-b border-slate-200 pb-4 mb-2">
        <p className="text-sm font-semibold text-ink">Hero-sektion</p>
        <p className="text-xs text-slate-500 mt-0.5">Den stora bannern längst upp på startsidan</p>
      </div>

      {field("Huvudrubrik (H1)", "hero_title", "t.ex. Profilering & Tryck för ditt företag")}
      {field("Underrubrik", "hero_subtitle", "t.ex. Vi hjälper företag med arbetskläder...", true)}
      {field("CTA-knapptext", "hero_cta_text", "t.ex. Se produkter")}
      {field("CTA-länk", "hero_cta_link", "/products")}

      <div className="flex items-center gap-3 pt-2">
        <button
          onClick={handleSave}
          disabled={status === "saving"}
          className="flex items-center gap-2 rounded-xl bg-ink px-5 py-2.5 text-sm font-medium text-white hover:bg-ink/90 disabled:opacity-60 transition-colors"
        >
          <Save size={15} />
          {status === "saving" ? "Sparar..." : "Spara ändringar"}
        </button>
        {status === "saved" && (
          <span className="flex items-center gap-1.5 text-sm text-green-600">
            <CheckCircle size={15} /> Sparat
          </span>
        )}
        {status === "error" && (
          <span className="flex items-center gap-1.5 text-sm text-red-600">
            <AlertCircle size={15} /> Kunde inte spara
          </span>
        )}
      </div>
    </div>
  );
}

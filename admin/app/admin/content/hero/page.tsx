import { HeroEditor } from "@/components/admin/hero-editor";
import { Panel } from "@/components/ui/panel";
import { fetchAdminContent } from "@/lib/api/server";

export const dynamic = "force-dynamic";

export default async function AdminHeroPage() {
  const content = await fetchAdminContent();

  return (
    <div className="space-y-6 max-w-3xl">
      <div>
        <p className="text-xs font-semibold uppercase tracking-[0.2em] text-steel">Frontend-innehåll</p>
        <h1 className="mt-1 text-2xl font-semibold text-ink">Startsida & Hero</h1>
        <p className="mt-1 text-sm text-slate-500">
          Redigera hero-sektionen på uniforma.livosys.se — rubrik, underrubrik, CTA och bild.
        </p>
      </div>

      <Panel>
        <p className="mb-4 text-xs text-slate-400 bg-amber-50 border border-amber-200 rounded-lg px-4 py-2.5">
          Ändringar sparas som utkast och publiceras när du klickar <strong>Publicera</strong> på publiceringssidan.
        </p>
        <HeroEditor initial={content} />
      </Panel>
    </div>
  );
}

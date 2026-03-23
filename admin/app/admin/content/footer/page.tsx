import { FooterEditor } from "@/components/admin/footer-editor";
import { Panel } from "@/components/ui/panel";
import { fetchAdminContent } from "@/lib/api/server";

export const dynamic = "force-dynamic";

export default async function AdminFooterPage() {
  const content = await fetchAdminContent();

  return (
    <div className="space-y-6 max-w-3xl">
      <div>
        <p className="text-xs font-semibold uppercase tracking-[0.2em] text-steel">Frontend-innehåll</p>
        <h1 className="mt-1 text-2xl font-semibold text-ink">Footer & Kontakt</h1>
        <p className="mt-1 text-sm text-slate-500">
          Redigera kontaktuppgifter, footer-text och sociala medielänkar för uniforma.livosys.se.
        </p>
      </div>
      <Panel>
        <FooterEditor initial={content} />
      </Panel>
    </div>
  );
}

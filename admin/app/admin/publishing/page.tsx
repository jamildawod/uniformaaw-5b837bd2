import { PublishingPanel } from "@/components/admin/publishing-panel";
import { Panel } from "@/components/ui/panel";
import { fetchSupplierSyncOverview, fetchAdminContent } from "@/lib/api/server";

export const dynamic = "force-dynamic";

export default async function AdminPublishingPage() {
  const [syncOverview, content] = await Promise.all([
    fetchSupplierSyncOverview(),
    fetchAdminContent(),
  ]);

  return (
    <div className="space-y-6 max-w-4xl">
      <div>
        <p className="text-xs font-semibold uppercase tracking-[0.2em] text-steel">Admin</p>
        <h1 className="mt-1 text-2xl font-semibold text-ink">Publicering</h1>
        <p className="mt-1 text-sm text-slate-500">
          Kontrollera vad som publiceras på uniforma.livosys.se. Sparade ändringar publiceras här.
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Panel>
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-steel">Innehåll</p>
          <h2 className="mt-1 text-lg font-semibold text-ink">Sidinnehåll</h2>
          <div className="mt-4 space-y-3 text-sm text-slate-600">
            <div className="flex justify-between border-b border-slate-100 pb-2">
              <span>Hero-rubrik</span>
              <span className="font-medium text-ink truncate ml-2 max-w-[160px]">
                {(content as { hero_title?: string } | null)?.hero_title ?? "—"}
              </span>
            </div>
            <div className="flex justify-between border-b border-slate-100 pb-2">
              <span>CTA-text</span>
              <span className="font-medium text-ink truncate ml-2 max-w-[160px]">
                {(content as { hero_cta_text?: string } | null)?.hero_cta_text ?? "—"}
              </span>
            </div>
            <div className="flex justify-between">
              <span>Footer-text</span>
              <span className="font-medium text-ink truncate ml-2 max-w-[160px]">
                {(content as { footer_text?: string } | null)?.footer_text ?? "—"}
              </span>
            </div>
          </div>
        </Panel>

        <Panel>
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-steel">Leverantörssynk</p>
          <h2 className="mt-1 text-lg font-semibold text-ink">Produktdata</h2>
          <div className="mt-4 space-y-3 text-sm text-slate-600">
            <div className="flex justify-between border-b border-slate-100 pb-2">
              <span>Status</span>
              <span className={`font-medium ${syncOverview?.last_sync_status === "success" ? "text-green-600" : "text-amber-600"}`}>
                {syncOverview?.last_sync_status ?? "Okänt"}
              </span>
            </div>
            <div className="flex justify-between border-b border-slate-100 pb-2">
              <span>Senaste synk</span>
              <span className="font-medium text-ink">
                {syncOverview?.last_sync_time
                  ? new Date(syncOverview.last_sync_time).toLocaleString("sv-SE")
                  : "Aldrig"}
              </span>
            </div>
            <div className="flex justify-between">
              <span>Importerade produkter</span>
              <span className="font-medium text-ink">{syncOverview?.products_imported ?? "—"}</span>
            </div>
          </div>
        </Panel>
      </div>

      <PublishingPanel syncLogs={syncOverview?.logs ?? []} />
    </div>
  );
}

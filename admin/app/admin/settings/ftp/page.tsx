import { FtpSettingsForm } from "@/components/admin/ftp-settings-form";
import { Panel } from "@/components/ui/panel";
import { fetchSupplierIntegration } from "@/lib/api/server";

export const dynamic = "force-dynamic";

export default async function AdminFtpPage() {
  const integration = await fetchSupplierIntegration();

  return (
    <div className="space-y-6 max-w-2xl">
      <div>
        <p className="text-xs font-semibold uppercase tracking-[0.2em] text-steel">Inställningar</p>
        <h1 className="mt-1 text-2xl font-semibold text-ink">FTP/SFTP-inställningar</h1>
        <p className="mt-1 text-sm text-slate-500">
          Anslutningsinställningar för filöverföring och leverantörssynk. Lösenord krypteras och visas aldrig i klartext.
        </p>
      </div>

      <Panel className="border border-amber-200 bg-amber-50/30">
        <p className="text-sm text-amber-800">
          <strong>Säkerhetsnotering:</strong> Prioritera SFTP (SSH) framför FTP. FTP skickar credentials okrypterat och bör undvikas i produktion.
        </p>
      </Panel>

      <Panel>
        <FtpSettingsForm initial={integration} />
      </Panel>
    </div>
  );
}

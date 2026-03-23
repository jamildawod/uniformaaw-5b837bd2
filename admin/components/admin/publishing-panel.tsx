"use client";

import { useState } from "react";
import { Send, RefreshCw, CheckCircle, AlertCircle, Clock } from "lucide-react";
import { Panel } from "@/components/ui/panel";

type SyncLog = {
  id: number;
  started_at: string;
  finished_at?: string | null;
  status: string;
  products_imported?: number | null;
  error_message?: string | null;
};

export function PublishingPanel({ syncLogs }: { syncLogs: SyncLog[] }) {
  const [syncStatus, setSyncStatus] = useState<"idle" | "running" | "done" | "error">("idle");
  const [syncResult, setSyncResult] = useState<string>("");

  const handleSync = async () => {
    setSyncStatus("running");
    setSyncResult("");
    try {
      const res = await fetch("/api/uniforma/admin/integrations/supplier/sync", { method: "POST" });
      const data = await res.json() as { products_imported?: number; message?: string };
      setSyncStatus("done");
      setSyncResult(data.message ?? `${data.products_imported ?? 0} produkter importerade`);
    } catch {
      setSyncStatus("error");
      setSyncResult("Synken misslyckades — kontrollera FTP/SFTP-inställningar");
    }
  };

  return (
    <div className="space-y-6">
      <Panel>
        <p className="text-xs font-semibold uppercase tracking-[0.2em] text-steel">Publicera</p>
        <h2 className="mt-1 text-lg font-semibold text-ink">Synka produktdata till frontend</h2>
        <p className="mt-2 text-sm text-slate-500">
          Kör en manuell synk för att importera senaste produktdata från leverantören och göra den tillgänglig på uniforma.livosys.se.
        </p>

        <div className="mt-5 flex flex-wrap items-center gap-3">
          <button
            onClick={handleSync}
            disabled={syncStatus === "running"}
            className="flex items-center gap-2 rounded-xl bg-ink px-6 py-2.5 text-sm font-medium text-white hover:bg-ink/90 disabled:opacity-60 transition-colors"
          >
            {syncStatus === "running" ? (
              <><RefreshCw size={15} className="animate-spin" /> Synkar...</>
            ) : (
              <><Send size={15} /> Kör synk nu</>
            )}
          </button>
          {syncStatus === "done" && (
            <span className="flex items-center gap-1.5 text-sm text-green-600">
              <CheckCircle size={15} /> {syncResult}
            </span>
          )}
          {syncStatus === "error" && (
            <span className="flex items-center gap-1.5 text-sm text-red-600">
              <AlertCircle size={15} /> {syncResult}
            </span>
          )}
        </div>
      </Panel>

      <Panel>
        <p className="text-xs font-semibold uppercase tracking-[0.2em] text-steel mb-4">Publiceringslogg</p>
        {syncLogs.length === 0 ? (
          <p className="text-sm text-slate-500">Inga synkar utförda ännu.</p>
        ) : (
          <div className="space-y-2">
            {syncLogs.slice(0, 10).map((log) => (
              <div
                key={log.id}
                className="flex items-start justify-between gap-4 rounded-xl border border-slate-100 p-4"
              >
                <div className="flex items-center gap-3">
                  {log.status === "success" ? (
                    <CheckCircle size={16} className="flex-shrink-0 text-green-500" />
                  ) : log.status === "running" ? (
                    <RefreshCw size={16} className="flex-shrink-0 animate-spin text-blue-500" />
                  ) : (
                    <AlertCircle size={16} className="flex-shrink-0 text-red-500" />
                  )}
                  <div>
                    <p className="text-sm font-medium text-ink capitalize">{log.status}</p>
                    {log.error_message && (
                      <p className="mt-0.5 text-xs text-red-500">{log.error_message}</p>
                    )}
                  </div>
                </div>
                <div className="flex-shrink-0 text-right">
                  <p className="text-xs text-slate-500 flex items-center gap-1">
                    <Clock size={11} />
                    {new Date(log.started_at).toLocaleString("sv-SE")}
                  </p>
                  {log.products_imported != null && (
                    <p className="text-xs text-slate-400">{log.products_imported} produkter</p>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </Panel>
    </div>
  );
}

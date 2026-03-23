import { UsersPanel } from "@/components/admin/users-panel";
import { Panel } from "@/components/ui/panel";

export const dynamic = "force-dynamic";

export default function AdminUsersPage() {
  return (
    <div className="space-y-6 max-w-3xl">
      <div>
        <p className="text-xs font-semibold uppercase tracking-[0.2em] text-steel">Inställningar</p>
        <h1 className="mt-1 text-2xl font-semibold text-ink">Användare & Roller</h1>
        <p className="mt-1 text-sm text-slate-500">
          Hantera admin-konton och åtkomsträttigheter. Admins har full tillgång, editors kan redigera innehåll och media.
        </p>
      </div>

      <Panel className="border border-slate-200 bg-slate-50/50">
        <div className="grid gap-4 sm:grid-cols-2 text-sm">
          <div>
            <p className="font-semibold text-ink">Admin</p>
            <p className="mt-1 text-slate-500">Full tillgång inklusive FTP/SFTP-inställningar, användare och publicering.</p>
          </div>
          <div>
            <p className="font-semibold text-ink">Editor</p>
            <p className="mt-1 text-slate-500">Kan redigera innehåll, produkter och bilder. Ej tillgång till känsliga systeminställningar.</p>
          </div>
        </div>
      </Panel>

      <UsersPanel />
    </div>
  );
}

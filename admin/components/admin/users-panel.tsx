"use client";

import { useState } from "react";
import { UserPlus, ShieldCheck, AlertCircle } from "lucide-react";
import { Panel } from "@/components/ui/panel";

// Stubbed users panel — connects to /api/v1/admin/users when endpoint exists
export function UsersPanel() {
  const [showInvite, setShowInvite] = useState(false);
  const [inviteEmail, setInviteEmail] = useState("");
  const [inviteRole, setInviteRole] = useState<"admin" | "editor">("editor");
  const [inviteStatus, setInviteStatus] = useState<"idle" | "sending" | "done" | "error">("idle");

  const handleInvite = async (e: React.FormEvent) => {
    e.preventDefault();
    setInviteStatus("sending");
    try {
      const res = await fetch("/api/uniforma/admin/users", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: inviteEmail, role: inviteRole }),
      });
      if (!res.ok) throw new Error();
      setInviteStatus("done");
      setInviteEmail("");
      setTimeout(() => { setInviteStatus("idle"); setShowInvite(false); }, 2000);
    } catch {
      setInviteStatus("error");
    }
  };

  return (
    <div className="space-y-5">
      <Panel>
        <div className="flex items-center justify-between mb-4">
          <p className="text-sm font-semibold text-ink">Administratörer</p>
          <button
            onClick={() => setShowInvite((s) => !s)}
            className="flex items-center gap-1.5 rounded-lg bg-ink px-3 py-2 text-xs font-medium text-white hover:bg-ink/90 transition-colors"
          >
            <UserPlus size={13} />
            Lägg till användare
          </button>
        </div>

        {showInvite && (
          <form onSubmit={handleInvite} className="mb-5 rounded-xl border border-slate-200 p-4 space-y-3">
            <p className="text-xs font-semibold text-steel uppercase tracking-wide">Ny användare</p>
            <div>
              <label className="block text-xs font-medium text-ink mb-1">E-post</label>
              <input
                type="email"
                required
                className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm focus:border-ink focus:outline-none"
                placeholder="namn@foretag.se"
                value={inviteEmail}
                onChange={(e) => setInviteEmail(e.target.value)}
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-ink mb-1">Roll</label>
              <select
                className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm focus:border-ink focus:outline-none bg-white"
                value={inviteRole}
                onChange={(e) => setInviteRole(e.target.value as "admin" | "editor")}
              >
                <option value="editor">Editor</option>
                <option value="admin">Admin</option>
              </select>
            </div>
            <div className="flex items-center gap-2">
              <button
                type="submit"
                disabled={inviteStatus === "sending"}
                className="rounded-lg bg-ink px-4 py-2 text-xs font-medium text-white hover:bg-ink/90 disabled:opacity-60"
              >
                {inviteStatus === "sending" ? "Skapar..." : "Skapa konto"}
              </button>
              {inviteStatus === "done" && (
                <span className="text-xs text-green-600 flex items-center gap-1">
                  <ShieldCheck size={13} /> Användaren skapades
                </span>
              )}
              {inviteStatus === "error" && (
                <span className="text-xs text-red-600 flex items-center gap-1">
                  <AlertCircle size={13} /> Kunde inte skapa
                </span>
              )}
            </div>
          </form>
        )}

        <div className="space-y-2">
          <div className="flex items-center gap-3 rounded-xl bg-slate-50 p-3 text-sm">
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-ink text-white text-xs font-bold">A</div>
            <div className="flex-1 min-w-0">
              <p className="font-medium text-ink text-sm">Administratörskonto</p>
              <p className="text-xs text-slate-500">Konfigurerat via miljövariabler</p>
            </div>
            <span className="flex items-center gap-1 rounded-full bg-ink/10 px-2 py-0.5 text-[10px] font-semibold uppercase text-ink">
              <ShieldCheck size={10} /> Admin
            </span>
          </div>
        </div>
      </Panel>

      <Panel className="border border-amber-200 bg-amber-50/30">
        <div className="flex gap-3 text-sm">
          <AlertCircle size={16} className="flex-shrink-0 mt-0.5 text-amber-600" />
          <div>
            <p className="font-medium text-amber-900">Användarhantering</p>
            <p className="mt-1 text-amber-700">
              Standardadminkontot konfigureras via <code className="rounded bg-amber-100 px-1 py-0.5 text-xs">DEFAULT_ADMIN_EMAIL</code> i{" "}
              <code className="rounded bg-amber-100 px-1 py-0.5 text-xs">.env</code>. Ytterligare konton registreras via{" "}
              <code className="rounded bg-amber-100 px-1 py-0.5 text-xs">/api/v1/auth/register</code>.
            </p>
          </div>
        </div>
      </Panel>
    </div>
  );
}

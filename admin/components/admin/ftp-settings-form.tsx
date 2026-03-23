"use client";

import { useState } from "react";
import { Save, CheckCircle, AlertCircle, Wifi, WifiOff, Eye, EyeOff } from "lucide-react";

type FtpFormData = {
  protocol: "sftp" | "ftp";
  host: string;
  port: number;
  username: string;
  password: string;
  private_key: string;
  remote_path: string;
  timeout_seconds: number;
};

type FtpInitial = {
  ftp_host?: string | null;
  ftp_username?: string | null;
  has_password?: boolean;
  pictures_path?: string;
  timeout_seconds?: number;
} | null;

export function FtpSettingsForm({ initial }: { initial: FtpInitial }) {
  const [form, setForm] = useState<FtpFormData>({
    protocol: "sftp",
    host: initial?.ftp_host ?? "",
    port: 22,
    username: initial?.ftp_username ?? "",
    password: "",
    private_key: "",
    remote_path: initial?.pictures_path ?? "/",
    timeout_seconds: initial?.timeout_seconds ?? 30,
  });
  const [showPassword, setShowPassword] = useState(false);
  const [saveStatus, setSaveStatus] = useState<"idle" | "saving" | "saved" | "error">("idle");
  const [testStatus, setTestStatus] = useState<"idle" | "testing" | "ok" | "fail">("idle");
  const [testMessage, setTestMessage] = useState("");

  const handleChange = (key: keyof FtpFormData, value: string | number) => {
    setForm((prev) => ({ ...prev, [key]: value }));
  };

  const handleTest = async () => {
    setTestStatus("testing");
    setTestMessage("");
    try {
      const res = await fetch("/api/uniforma/admin/integrations/supplier/test", { method: "POST" });
      const data = await res.json() as { ok: boolean; message?: string };
      setTestStatus(data.ok ? "ok" : "fail");
      setTestMessage(data.message ?? "");
    } catch {
      setTestStatus("fail");
      setTestMessage("Nätverksfel — kunde inte nå servern");
    }
  };

  const handleSave = async () => {
    setSaveStatus("saving");
    try {
      const res = await fetch("/api/uniforma/admin/integrations/supplier", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          ftp_host: form.host,
          ftp_username: form.username,
          ftp_password: form.password || undefined,
          pictures_path: form.remote_path,
          product_data_path: form.remote_path,
          stock_path: form.remote_path,
          sync_enabled: true,
          sync_hour: 2,
          timeout_seconds: form.timeout_seconds,
        }),
      });
      if (!res.ok) throw new Error();
      setSaveStatus("saved");
      setTimeout(() => setSaveStatus("idle"), 3000);
    } catch {
      setSaveStatus("error");
    }
  };

  return (
    <div className="space-y-6">
      {/* Protocol */}
      <div>
        <label className="block text-sm font-medium text-ink mb-2">Protokoll</label>
        <div className="flex gap-3">
          {(["sftp", "ftp"] as const).map((p) => (
            <button
              key={p}
              type="button"
              onClick={() => {
                handleChange("protocol", p);
                handleChange("port", p === "sftp" ? 22 : 21);
              }}
              className={`flex-1 rounded-xl border px-4 py-3 text-sm font-medium transition ${
                form.protocol === p
                  ? "border-ink bg-ink text-white"
                  : "border-slate-200 text-slate-600 hover:border-slate-300"
              }`}
            >
              {p.toUpperCase()}
              {p === "sftp" && (
                <span className="ml-2 rounded-full bg-green-100 px-1.5 py-0.5 text-[9px] font-semibold text-green-700 uppercase">
                  Rekommenderat
                </span>
              )}
            </button>
          ))}
        </div>
      </div>

      {/* Connection */}
      <div className="grid gap-4 sm:grid-cols-[1fr_120px]">
        <div>
          <label className="block text-sm font-medium text-ink mb-1.5">Host / IP</label>
          <input
            type="text"
            className="w-full rounded-xl border border-slate-200 px-4 py-3 text-sm focus:border-ink focus:outline-none focus:ring-1 focus:ring-ink"
            placeholder="partnerftp.example.com"
            value={form.host}
            onChange={(e) => handleChange("host", e.target.value)}
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-ink mb-1.5">Port</label>
          <input
            type="number"
            className="w-full rounded-xl border border-slate-200 px-4 py-3 text-sm focus:border-ink focus:outline-none focus:ring-1 focus:ring-ink"
            value={form.port}
            onChange={(e) => handleChange("port", parseInt(e.target.value, 10))}
          />
        </div>
      </div>

      {/* Credentials */}
      <div>
        <label className="block text-sm font-medium text-ink mb-1.5">Användarnamn</label>
        <input
          type="text"
          className="w-full rounded-xl border border-slate-200 px-4 py-3 text-sm focus:border-ink focus:outline-none focus:ring-1 focus:ring-ink"
          placeholder="ftpuser"
          value={form.username}
          onChange={(e) => handleChange("username", e.target.value)}
          autoComplete="off"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-ink mb-1.5">
          Lösenord
          {initial?.has_password && (
            <span className="ml-2 text-xs font-normal text-slate-500">(ett lösenord är sparat — lämna tomt för att behålla det)</span>
          )}
        </label>
        <div className="relative">
          <input
            type={showPassword ? "text" : "password"}
            className="w-full rounded-xl border border-slate-200 px-4 py-3 pr-10 text-sm focus:border-ink focus:outline-none focus:ring-1 focus:ring-ink"
            placeholder={initial?.has_password ? "••••••••" : "Ange lösenord"}
            value={form.password}
            onChange={(e) => handleChange("password", e.target.value)}
            autoComplete="new-password"
          />
          <button
            type="button"
            onClick={() => setShowPassword((s) => !s)}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
          >
            {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
          </button>
        </div>
        <p className="mt-1 text-xs text-slate-400">Lösenordet sparas krypterat och visas aldrig i klartext.</p>
      </div>

      {/* Remote path */}
      <div>
        <label className="block text-sm font-medium text-ink mb-1.5">Remote path (rotsökväg)</label>
        <input
          type="text"
          className="w-full rounded-xl border border-slate-200 px-4 py-3 text-sm focus:border-ink focus:outline-none focus:ring-1 focus:ring-ink"
          placeholder="/"
          value={form.remote_path}
          onChange={(e) => handleChange("remote_path", e.target.value)}
        />
      </div>

      {/* Timeout */}
      <div>
        <label className="block text-sm font-medium text-ink mb-1.5">Timeout (sekunder)</label>
        <input
          type="number"
          className="w-32 rounded-xl border border-slate-200 px-4 py-3 text-sm focus:border-ink focus:outline-none focus:ring-1 focus:ring-ink"
          value={form.timeout_seconds}
          onChange={(e) => handleChange("timeout_seconds", parseInt(e.target.value, 10))}
        />
      </div>

      {/* Actions */}
      <div className="flex flex-wrap items-center gap-3 pt-2 border-t border-slate-200">
        <button
          type="button"
          onClick={handleTest}
          disabled={testStatus === "testing" || !form.host}
          className="flex items-center gap-2 rounded-xl border border-slate-200 px-5 py-2.5 text-sm font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-60 transition-colors"
        >
          {testStatus === "testing" ? (
            <><span className="h-4 w-4 animate-spin rounded-full border-2 border-slate-400 border-t-transparent" /> Testar...</>
          ) : testStatus === "ok" ? (
            <><Wifi size={15} className="text-green-600" /> Anslutning OK</>
          ) : testStatus === "fail" ? (
            <><WifiOff size={15} className="text-red-600" /> Misslyckades</>
          ) : (
            <><Wifi size={15} /> Testa anslutning</>
          )}
        </button>
        {testMessage && (
          <span className={`text-xs ${testStatus === "ok" ? "text-green-600" : "text-red-600"}`}>{testMessage}</span>
        )}

        <button
          type="button"
          onClick={handleSave}
          disabled={saveStatus === "saving"}
          className="flex items-center gap-2 rounded-xl bg-ink px-5 py-2.5 text-sm font-medium text-white hover:bg-ink/90 disabled:opacity-60 transition-colors"
        >
          <Save size={15} />
          {saveStatus === "saving" ? "Sparar..." : "Spara inställningar"}
        </button>

        {saveStatus === "saved" && (
          <span className="flex items-center gap-1.5 text-sm text-green-600">
            <CheckCircle size={15} /> Sparat
          </span>
        )}
        {saveStatus === "error" && (
          <span className="flex items-center gap-1.5 text-sm text-red-600">
            <AlertCircle size={15} /> Kunde inte spara
          </span>
        )}
      </div>
    </div>
  );
}

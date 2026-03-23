"use client";

import { useCallback, useRef, useState } from "react";

import type { PimImportRun } from "@/lib/types/pim";
import type { UploadResponse } from "@/lib/types/products";

interface CsvImportPanelProps {
  initialLogs: PimImportRun[];
}

type StatusMessage = { type: "success" | "error" | "info"; text: string };

const suppliers = [{ value: "hejco", label: "Hejco" }];

export function CsvImportPanel({ initialLogs }: CsvImportPanelProps) {
  const [logs, setLogs] = useState<PimImportRun[]>(initialLogs);
  const [selectedSupplier, setSelectedSupplier] = useState(suppliers[0].value);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadedFilename, setUploadedFilename] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const [importRunning, setImportRunning] = useState(false);
  const [dragActive, setDragActive] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [statusMessage, setStatusMessage] = useState<StatusMessage | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const refreshLogs = useCallback(async () => {
    const response = await fetch("/api/uniforma/api/v1/admin/pim/imports", {
      cache: "no-store",
      credentials: "include"
    });

    if (!response.ok) {
      throw new Error("Unable to refresh import logs.");
    }

    const payload = (await response.json()) as PimImportRun[];
    setLogs(payload);
  }, []);

  const uploadCsv = useCallback(async (file: File) => {
    const isCsv = file.name.toLowerCase().endsWith(".csv") || file.type === "text/csv";
    if (!isCsv) {
      setUploadError("Only CSV files are supported.");
      setUploadedFilename(null);
      return;
    }

    setUploading(true);
    setUploadError(null);
    setStatusMessage(null);
    setUploadedFilename(null);

    try {
      const form = new FormData();
      form.set("file", file);

      const response = await fetch("/api/uniforma/api/v1/admin/media/upload", {
        method: "POST",
        body: form,
        credentials: "include"
      });

      if (!response.ok) {
        throw new Error("Upload failed.");
      }

      const data = (await response.json()) as UploadResponse;
      setUploadedFilename(data.filename);
      setStatusMessage({ type: "success", text: "CSV uploaded and ready." });
    } catch (error) {
      setUploadError(error instanceof Error ? error.message : "Upload failed.");
    } finally {
      setUploading(false);
    }
  }, []);

  const handleFile = useCallback(
    (file: File) => {
      setSelectedFile(file);
      void uploadCsv(file);
    },
    [uploadCsv]
  );

  const runImport = useCallback(async () => {
    if (!uploadedFilename) {
      setStatusMessage({ type: "error", text: "Upload a CSV before running import." });
      return;
    }

    setImportRunning(true);
    setStatusMessage(null);

    try {
      const response = await fetch("/api/uniforma/api/v1/admin/pim/run-import", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        credentials: "include",
        body: JSON.stringify({ supplier: selectedSupplier, file: uploadedFilename })
      });

      if (!response.ok) {
        const errorText = (await response.text()) || response.statusText;
        throw new Error(errorText);
      }

      setStatusMessage({ type: "success", text: "Import queued. Logs refreshed." });
      setSelectedFile(null);
      setUploadedFilename(null);
      try {
        await refreshLogs();
      } catch (refreshError) {
        console.error(refreshError);
      }
    } catch (error) {
      setStatusMessage({ type: "error", text: error instanceof Error ? error.message : "Import failed." });
    } finally {
      setImportRunning(false);
    }
  }, [refreshLogs, selectedSupplier, uploadedFilename]);

  return (
    <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_minmax(0,0.8fr)]">
      <div className="space-y-6">
        <div
          className={`relative flex cursor-pointer flex-col items-center justify-center rounded-3xl border-2 border-dashed px-5 py-10 text-center transition-colors ${
            dragActive
              ? "border-ink bg-slate-100"
              : "border-slate-200 bg-white/70 hover:border-slate-300"
          }`}
          onClick={() => fileInputRef.current?.click()}
          onDragEnter={(event) => {
            event.preventDefault();
            setDragActive(true);
          }}
          onDragLeave={(event) => {
            event.preventDefault();
            setDragActive(false);
          }}
          onDragOver={(event) => event.preventDefault()}
          onDrop={(event) => {
            event.preventDefault();
            setDragActive(false);
            const file = event.dataTransfer.files[0];
            if (file) {
              handleFile(file);
            }
          }}
        >
          <input
            ref={fileInputRef}
            type="file"
            className="hidden"
            accept=".csv,text/csv"
            disabled={uploading}
            onChange={(event) => {
              const file = event.currentTarget.files?.[0];
              if (file) {
                handleFile(file);
              }
              event.currentTarget.value = "";
            }}
          />

          <div className="space-y-2">
            <p className="text-sm font-semibold text-ink">Drag & drop a CSV file</p>
            <p className="text-xs uppercase tracking-[0.3em] text-slate-400">.csv only</p>
            <p className="text-sm text-slate-500">
              {uploadedFilename ? uploadedFilename : selectedFile?.name ? `Selected: ${selectedFile.name}` : "Drop file or click to browse"}
            </p>
          </div>

          {uploading ? (
            <div className="absolute inset-0 flex items-center justify-center rounded-3xl bg-white/70">
              <div className="flex items-center gap-2">
                <span className="h-5 w-5 animate-spin rounded-full border-2 border-ink border-t-transparent" />
                <p className="text-xs font-semibold text-ink">Uploading CSV…</p>
              </div>
            </div>
          ) : null}
        </div>

        {uploadError ? <p className="text-xs font-semibold text-rose-600">{uploadError}</p> : null}

        <div className="flex flex-col gap-3 rounded-2xl border border-slate-200 bg-slate-50/90 p-4">
          <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
            <label className="text-sm text-slate-500">Supplier</label>
            <select
              className="max-w-xs rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-700 shadow-sm"
              value={selectedSupplier}
              onChange={(event) => setSelectedSupplier(event.target.value)}
            >
              {suppliers.map((supplier) => (
                <option key={supplier.value} value={supplier.value}>
                  {supplier.label}
                </option>
              ))}
            </select>
          </div>

          <button
            className="flex items-center justify-center gap-2 rounded-2xl bg-ink px-6 py-3 text-sm font-semibold text-white transition hover:bg-ink/90 disabled:cursor-not-allowed disabled:bg-slate-400"
            disabled={!uploadedFilename || uploading || importRunning}
            onClick={() => void runImport()}
            type="button"
          >
            {importRunning ? (
              <span className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
            ) : null}
            Run import
          </button>

          {statusMessage ? (
            <p className={`text-xs font-semibold ${statusMessage.type === "error" ? "text-rose-600" : "text-emerald-600"}`}>
              {statusMessage.text}
            </p>
          ) : null}

          {importRunning && (
            <p className="text-xs text-slate-500">This may take a few moments. The log will refresh automatically.</p>
          )}
        </div>
      </div>

      <div className="space-y-4">
        <div className="space-y-4 rounded-2xl border border-slate-200 bg-gradient-to-br from-white to-slate-50 p-5 shadow-sm">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-400">Import logs</p>
            <h3 className="text-lg font-semibold text-ink">Recent runs</h3>
          </div>
          <div className="space-y-3">
            {logs.length === 0 ? (
              <p className="text-sm text-slate-500">No import history yet.</p>
            ) : (
              logs.slice(0, 6).map((run) => (
                <article key={run.id} className="rounded-2xl border border-slate-200 bg-white/90 p-4 shadow-[0_2px_20px_rgba(15,23,42,0.05)]">
                  <div className="flex items-center justify-between gap-3">
                    <div>
                      <p className="text-xs uppercase tracking-[0.3em] text-slate-400">{run.source?.name ?? "Manual"}</p>
                      <p className="text-sm font-semibold text-ink">{run.status}</p>
                    </div>
                    <p className="text-xs text-slate-500">{new Date(run.started_at).toLocaleString()}</p>
                  </div>
                  <p className="mt-2 text-xs text-slate-500">
                    Processed {run.records_processed} · Created {run.records_created} · Updated {run.records_updated}
                  </p>
                  {run.error_log ? (
                    <p className="mt-3 text-xs text-rose-600 whitespace-pre-line">{run.error_log}</p>
                  ) : null}
                </article>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

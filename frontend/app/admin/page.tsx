"use client";

import { FormEvent, useEffect, useState } from "react";

import { getCleanArticleNumber } from "@/lib/article-number";
import { API_URL } from "@/lib/api";

type Product = {
  id: string;
  name: string;
  article_number: string | null;
  item_no: string | null;
  external_id: string | null;
};

type AuthResponse = {
  access_token: string;
  token_type: string;
};

type PimSummary = {
  total_items: number;
  active_items: number;
  other_items: number;
  latest_imported_at: string | null;
  latest_source_file_name: string | null;
};

type PimPreviewRow = {
  item_no: string;
  lifecycle_status: string;
  is_visible: boolean;
};

type PimPreview = {
  source_file_name: string;
  total_rows: number;
  importable_rows: number;
  active_count: number;
  other_status_count: number;
  skipped_count: number;
  preview_rows: PimPreviewRow[];
};

type PimImportResponse = PimPreview & {
  imported_items: number;
  summary: PimSummary;
};

const PRODUCTS_URL = `${API_URL}/products?limit=200`;
const SUPER_DEALS_URL = `${API_URL}/admin/super-deals`;
const LOGIN_URL = `${API_URL}/auth/login`;
const PIM_PREVIEW_URL = `${API_URL}/admin/pim-status/preview`;
const PIM_IMPORT_URL = `${API_URL}/admin/pim-status/import`;
const PIM_SUMMARY_URL = `${API_URL}/admin/pim-status/summary`;
const STORAGE_TOKEN_KEY = "uniforma.admin.access-token";
const STORAGE_EMAIL_KEY = "uniforma.admin.email";

function getErrorMessage(error: unknown, fallback: string): string {
  return error instanceof Error ? error.message : fallback;
}

function formatDate(value: string | null): string {
  if (!value) return "Ingen import ännu";

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return new Intl.DateTimeFormat("sv-SE", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(date);
}

function normalizeProducts(data: unknown): Product[] {
  if (!Array.isArray(data)) {
    return [];
  }

  return data
    .map((item) => {
      if (!item || typeof item !== "object") {
        return null;
      }

      const rawId = "id" in item ? (item as any).id : null;
      const rawName = "name" in item ? (item as any).name : null;
      const rawArticleNumber = "article_number" in item ? (item as any).article_number : null;
      const rawItemNo = "item_no" in item ? (item as any).item_no : null;
      const rawExternalId = "external_id" in item ? (item as any).external_id : null;

      if (
        (typeof rawId !== "string" && typeof rawId !== "number") ||
        typeof rawName !== "string"
      ) {
        return null;
      }

      return {
        id: String(rawId),
        name: rawName,
        article_number: typeof rawArticleNumber === "string" ? rawArticleNumber : null,
        item_no: typeof rawItemNo === "string" ? rawItemNo : null,
        external_id: typeof rawExternalId === "string" ? rawExternalId : null,
      };
    })
    .filter((product): product is Product => product !== null);
}

export default function AdminPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [token, setToken] = useState("");
  const [isBootstrapped, setIsBootstrapped] = useState(false);
  const [isAuthenticating, setIsAuthenticating] = useState(false);
  const [products, setProducts] = useState<Product[]>([]);
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [pimFile, setPimFile] = useState<File | null>(null);
  const [pimPreview, setPimPreview] = useState<PimPreview | null>(null);
  const [pimSummary, setPimSummary] = useState<PimSummary | null>(null);
  const [pimError, setPimError] = useState("");
  const [pimMessage, setPimMessage] = useState("");
  const [isPreviewing, setIsPreviewing] = useState(false);
  const [isImporting, setIsImporting] = useState(false);
  const isLoggedIn = token.length > 0;

  useEffect(() => {
    const storedToken = window.localStorage.getItem(STORAGE_TOKEN_KEY) ?? "";
    const storedEmail = window.localStorage.getItem(STORAGE_EMAIL_KEY) ?? "";

    if (storedToken) {
      setToken(storedToken);
    }
    if (storedEmail) {
      setEmail(storedEmail);
    }

    setIsBootstrapped(true);
  }, []);

  useEffect(() => {
    if (!isLoggedIn) {
      setProducts([]);
      setSelectedIds([]);
      setPimSummary(null);
      return;
    }

    void fetchProducts();
    void fetchPimSummary();
  }, [isLoggedIn]);

  const clearSession = () => {
    window.localStorage.removeItem(STORAGE_TOKEN_KEY);
    window.localStorage.removeItem(STORAGE_EMAIL_KEY);
    setToken("");
  };

  const readJsonError = async (response: Response, fallback: string) => {
    const payload = await response.json().catch(() => null);
    const detail =
      payload && typeof payload === "object" && "detail" in payload
        ? (payload as { detail?: unknown }).detail
        : null;

    if (typeof detail === "string" && detail.trim()) {
      return detail;
    }

    return fallback;
  };

  const authorizedFetch = async (url: string, init?: RequestInit) => {
    const response = await fetch(url, {
      ...init,
      headers: {
        ...(init?.headers ?? {}),
        Authorization: `Bearer ${token}`,
      },
    });

    if (response.status === 401 || response.status === 403) {
      clearSession();
      throw new Error("Adminsessionen har gått ut. Logga in igen.");
    }

    return response;
  };

  const fetchProducts = async () => {
    setIsLoading(true);
    setError("");

    try {
      const response = await fetch(PRODUCTS_URL, {
        method: "GET",
        cache: "no-store",
      });

      if (!response.ok) {
        throw new Error(`Kunde inte hämta produkter (${response.status})`);
      }

      const json = await response.json();
      setProducts(normalizeProducts(json));
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Fel vid hämtning av produkter"
      );
      setProducts([]);
    } finally {
      setIsLoading(false);
    }
  };

  const fetchPimSummary = async () => {
    setPimError("");

    try {
      const response = await authorizedFetch(PIM_SUMMARY_URL, {
        method: "GET",
        cache: "no-store",
      });

      if (!response.ok) {
        throw new Error(await readJsonError(response, `Kunde inte läsa PIM-status (${response.status})`));
      }

      const json = (await response.json()) as PimSummary;
      setPimSummary(json);
    } catch (err) {
      setPimError(getErrorMessage(err, "Fel vid hämtning av PIM-status"));
      setPimSummary(null);
    }
  };

  const handleLogin = async (e: FormEvent) => {
    e.preventDefault();
    setError("");
    setMessage("");
    setIsAuthenticating(true);

    try {
      const body = new URLSearchParams();
      body.set("username", email);
      body.set("password", password);

      const response = await fetch(LOGIN_URL, {
        method: "POST",
        headers: {
          "Content-Type": "application/x-www-form-urlencoded",
        },
        body,
      });

      if (!response.ok) {
        throw new Error(await readJsonError(response, `Kunde inte logga in (${response.status})`));
      }

      const json = (await response.json()) as AuthResponse;
      window.localStorage.setItem(STORAGE_TOKEN_KEY, json.access_token);
      window.localStorage.setItem(STORAGE_EMAIL_KEY, email);
      setToken(json.access_token);
      setPassword("");
      setMessage("Inloggad.");
    } catch (err) {
      setError(getErrorMessage(err, "Fel vid inloggning"));
    } finally {
      setIsAuthenticating(false);
    }
  };

  const toggleSelection = (id: string) => {
    setSelectedIds((prev) =>
      prev.includes(id)
        ? prev.filter((x) => x !== id)
        : [...prev, id]
    );
  };

  const saveSuperDeals = async () => {
    setIsSaving(true);
    setError("");
    setMessage("");

    try {
      const res = await authorizedFetch(SUPER_DEALS_URL, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(selectedIds),
      });

      if (!res.ok) {
        throw new Error(`Kunde inte spara (${res.status})`);
      }

      setMessage("Super deals sparade!");
    } catch (err) {
      setError(getErrorMessage(err, "Fel vid sparning"));
    } finally {
      setIsSaving(false);
    }
  };

  const submitPimFile = async <T,>(url: string): Promise<T> => {
    if (!pimFile) {
      throw new Error("Välj en CSV- eller XLSX-fil först.");
    }

    const formData = new FormData();
    formData.append("file", pimFile);

    const response = await authorizedFetch(url, {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      throw new Error(await readJsonError(response, `Kunde inte läsa filen (${response.status})`));
    }

    return response.json() as Promise<T>;
  };

  const previewPimImport = async () => {
    setIsPreviewing(true);
    setPimError("");
    setPimMessage("");

    try {
      const preview = await submitPimFile<PimPreview>(PIM_PREVIEW_URL);
      setPimPreview(preview);
      setPimMessage("Preview uppdaterad.");
    } catch (err) {
      setPimError(getErrorMessage(err, "Fel vid preview"));
      setPimPreview(null);
    } finally {
      setIsPreviewing(false);
    }
  };

  const importPimStatuses = async () => {
    setIsImporting(true);
    setPimError("");
    setPimMessage("");

    try {
      const result = await submitPimFile<PimImportResponse>(PIM_IMPORT_URL);
      setPimPreview(result);
      setPimSummary(result.summary);
      setPimMessage(`Importerade ${result.imported_items} artikelnummer.`);
    } catch (err) {
      setPimError(getErrorMessage(err, "Fel vid import"));
    } finally {
      setIsImporting(false);
    }
  };

  if (!isBootstrapped) {
    return <div className="p-6 text-sm text-stone-500">Laddar admin...</div>;
  }

  if (!isLoggedIn) {
    return (
      <div className="min-h-screen bg-stone-100 px-6 py-10">
        <div className="mx-auto max-w-md rounded-3xl border border-stone-200 bg-white p-8 shadow-sm">
          <h1 className="text-2xl font-semibold text-stone-950">Uniforma Admin</h1>
          <p className="mt-2 text-sm text-stone-500">
            Logga in med backend-admin för att hantera super deals och PIM-status.
          </p>
          <form onSubmit={handleLogin} className="mt-6 space-y-4">
            <label className="block">
              <span className="mb-1 block text-sm font-medium text-stone-700">E-post</span>
              <input
                type="email"
                placeholder="admin@uniforma.se"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                className="w-full rounded-xl border border-stone-300 px-4 py-3 text-sm outline-none transition focus:border-stone-950"
                autoComplete="username"
                required
              />
            </label>
            <label className="block">
              <span className="mb-1 block text-sm font-medium text-stone-700">Lösenord</span>
              <input
                type="password"
                placeholder="Lösenord"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                className="w-full rounded-xl border border-stone-300 px-4 py-3 text-sm outline-none transition focus:border-stone-950"
                autoComplete="current-password"
                required
              />
            </label>
            <button
              type="submit"
              disabled={isAuthenticating}
              className="w-full rounded-xl bg-stone-950 px-4 py-3 text-sm font-semibold text-white transition hover:bg-stone-800 disabled:cursor-not-allowed disabled:bg-stone-400"
            >
              {isAuthenticating ? "Loggar in..." : "Logga in"}
            </button>
          </form>
          {error && <p className="mt-4 text-sm text-red-600">{error}</p>}
          {message && <p className="mt-4 text-sm text-emerald-600">{message}</p>}
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-stone-100 px-6 py-10">
      <div className="mx-auto max-w-6xl space-y-8">
        <div className="flex flex-wrap items-start justify-between gap-4 rounded-3xl border border-stone-200 bg-white p-8 shadow-sm">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-stone-400">
              Admin
            </p>
            <h1 className="mt-2 text-3xl font-semibold text-stone-950">Super Deals och PIM Status Import</h1>
            <p className="mt-2 text-sm text-stone-500">
              Inloggad som {email || "admin"}.
            </p>
          </div>
          <button
            onClick={clearSession}
            className="rounded-xl border border-stone-300 px-4 py-2 text-sm font-medium text-stone-700 transition hover:border-stone-950 hover:text-stone-950"
          >
            Logga ut
          </button>
        </div>

        <section className="rounded-3xl border border-stone-200 bg-white p-8 shadow-sm">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <h2 className="text-xl font-semibold text-stone-950">Super Deals</h2>
              <p className="mt-1 text-sm text-stone-500">
                Välj vilka produkter som ska ligga i super deals-listan.
              </p>
            </div>
            <div className="flex flex-wrap gap-3">
              <button
                onClick={fetchProducts}
                className="rounded-xl border border-stone-300 px-4 py-2 text-sm font-medium text-stone-700 transition hover:border-stone-950 hover:text-stone-950"
              >
                {isLoading ? "Laddar..." : "Ladda produkter"}
              </button>
              <button
                onClick={saveSuperDeals}
                disabled={isSaving}
                className="rounded-xl bg-stone-950 px-4 py-2 text-sm font-semibold text-white transition hover:bg-stone-800 disabled:cursor-not-allowed disabled:bg-stone-400"
              >
                {isSaving ? "Sparar..." : "Spara super deals"}
              </button>
            </div>
          </div>

          {error && <p className="mt-4 text-sm text-red-600">{error}</p>}
          {message && <p className="mt-4 text-sm text-emerald-600">{message}</p>}

          <div className="mt-6 grid gap-3 md:grid-cols-2 xl:grid-cols-3">
            {products.map((product) => {
              const articleNumber = getCleanArticleNumber(product);

              return (
                <label
                  key={product.id}
                  className="flex items-start gap-3 rounded-2xl border border-stone-200 p-4 transition hover:border-stone-400"
                >
                  <input
                    type="checkbox"
                    checked={selectedIds.includes(product.id)}
                    onChange={() => toggleSelection(product.id)}
                    className="mt-1 h-4 w-4 rounded border-stone-300"
                  />
                  <span>
                    <span className="block text-sm font-medium text-stone-900">{product.name}</span>
                    {articleNumber && (
                      <span className="mt-1 block text-xs text-stone-500">Art.nr: {articleNumber}</span>
                    )}
                  </span>
                </label>
              );
            })}
          </div>
          {!products.length && !isLoading && (
            <p className="mt-6 text-sm text-stone-500">Inga produkter hämtades.</p>
          )}
        </section>

        <section className="rounded-3xl border border-stone-200 bg-white p-8 shadow-sm">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <h2 className="text-xl font-semibold text-stone-950">PIM Status Import</h2>
              <p className="mt-1 text-sm text-stone-500">
                Ladda upp en CSV- eller XLSX-fil med <code>ItemNo</code> och <code>ProductLifeCycleStatus</code>.
              </p>
            </div>
            <button
              onClick={fetchPimSummary}
              className="rounded-xl border border-stone-300 px-4 py-2 text-sm font-medium text-stone-700 transition hover:border-stone-950 hover:text-stone-950"
            >
              Uppdatera status
            </button>
          </div>

          <div className="mt-6 grid gap-4 md:grid-cols-4">
            <div className="rounded-2xl bg-stone-100 p-4">
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-stone-400">Totalt</p>
              <p className="mt-2 text-2xl font-semibold text-stone-950">{pimSummary?.total_items ?? 0}</p>
            </div>
            <div className="rounded-2xl bg-emerald-50 p-4">
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-emerald-600">Active</p>
              <p className="mt-2 text-2xl font-semibold text-emerald-700">{pimSummary?.active_items ?? 0}</p>
            </div>
            <div className="rounded-2xl bg-amber-50 p-4">
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-amber-600">Övriga</p>
              <p className="mt-2 text-2xl font-semibold text-amber-700">{pimSummary?.other_items ?? 0}</p>
            </div>
            <div className="rounded-2xl bg-stone-100 p-4">
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-stone-400">Senaste import</p>
              <p className="mt-2 text-sm font-medium text-stone-950">
                {formatDate(pimSummary?.latest_imported_at ?? null)}
              </p>
              {pimSummary?.latest_source_file_name && (
                <p className="mt-1 text-xs text-stone-500">{pimSummary.latest_source_file_name}</p>
              )}
            </div>
          </div>

          <div className="mt-6 rounded-2xl border border-dashed border-stone-300 p-5">
            <label className="block">
              <span className="mb-2 block text-sm font-medium text-stone-700">Välj fil</span>
              <input
                type="file"
                accept=".csv,.xlsx"
                onChange={(event) => {
                  setPimFile(event.target.files?.[0] ?? null);
                  setPimPreview(null);
                  setPimError("");
                  setPimMessage("");
                }}
                className="block w-full text-sm text-stone-600"
              />
            </label>
            <div className="mt-4 flex flex-wrap gap-3">
              <button
                onClick={previewPimImport}
                disabled={!pimFile || isPreviewing}
                className="rounded-xl border border-stone-300 px-4 py-2 text-sm font-medium text-stone-700 transition hover:border-stone-950 hover:text-stone-950 disabled:cursor-not-allowed disabled:border-stone-200 disabled:text-stone-400"
              >
                {isPreviewing ? "Läser preview..." : "Preview"}
              </button>
              <button
                onClick={importPimStatuses}
                disabled={!pimFile || isImporting}
                className="rounded-xl bg-stone-950 px-4 py-2 text-sm font-semibold text-white transition hover:bg-stone-800 disabled:cursor-not-allowed disabled:bg-stone-400"
              >
                {isImporting ? "Importerar..." : "Importera"}
              </button>
            </div>
          </div>

          {pimError && <p className="mt-4 text-sm text-red-600">{pimError}</p>}
          {pimMessage && <p className="mt-4 text-sm text-emerald-600">{pimMessage}</p>}

          {pimPreview && (
            <div className="mt-6 space-y-4">
              <div className="grid gap-4 md:grid-cols-4">
                <div className="rounded-2xl bg-stone-100 p-4">
                  <p className="text-xs font-semibold uppercase tracking-[0.18em] text-stone-400">Rader</p>
                  <p className="mt-2 text-2xl font-semibold text-stone-950">{pimPreview.total_rows}</p>
                </div>
                <div className="rounded-2xl bg-emerald-50 p-4">
                  <p className="text-xs font-semibold uppercase tracking-[0.18em] text-emerald-600">Active</p>
                  <p className="mt-2 text-2xl font-semibold text-emerald-700">{pimPreview.active_count}</p>
                </div>
                <div className="rounded-2xl bg-amber-50 p-4">
                  <p className="text-xs font-semibold uppercase tracking-[0.18em] text-amber-600">Övriga</p>
                  <p className="mt-2 text-2xl font-semibold text-amber-700">{pimPreview.other_status_count}</p>
                </div>
                <div className="rounded-2xl bg-stone-100 p-4">
                  <p className="text-xs font-semibold uppercase tracking-[0.18em] text-stone-400">Importbara</p>
                  <p className="mt-2 text-2xl font-semibold text-stone-950">{pimPreview.importable_rows}</p>
                  <p className="mt-1 text-xs text-stone-500">Skippade: {pimPreview.skipped_count}</p>
                </div>
              </div>

              <div className="overflow-hidden rounded-2xl border border-stone-200">
                <div className="border-b border-stone-200 bg-stone-50 px-4 py-3 text-sm font-medium text-stone-700">
                  Preview: {pimPreview.source_file_name}
                </div>
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-stone-200 text-sm">
                    <thead className="bg-white text-left text-stone-500">
                      <tr>
                        <th className="px-4 py-3 font-medium">ItemNo</th>
                        <th className="px-4 py-3 font-medium">Status</th>
                        <th className="px-4 py-3 font-medium">Synlig</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-stone-200 bg-white">
                      {pimPreview.preview_rows.map((row) => (
                        <tr key={`${row.item_no}-${row.lifecycle_status}`}>
                          <td className="px-4 py-3 font-mono text-xs text-stone-800">{row.item_no}</td>
                          <td className="px-4 py-3 text-stone-600">{row.lifecycle_status || "(tom)"}</td>
                          <td className="px-4 py-3">
                            <span
                              className={`inline-flex rounded-full px-2.5 py-1 text-xs font-semibold ${
                                row.is_visible
                                  ? "bg-emerald-100 text-emerald-700"
                                  : "bg-stone-100 text-stone-600"
                              }`}
                            >
                              {row.is_visible ? "Active" : "Dold"}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}
        </section>
      </div>
    </div>
  );
}

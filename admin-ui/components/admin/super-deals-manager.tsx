"use client";

import { useEffect, useState } from "react";

import { EmptyState } from "@/components/ui/empty-state";
import type { AdminProduct } from "@/lib/types/products";

type SuperDealProduct = {
  id: string;
};

function getPrimarySku(product: AdminProduct): string {
  return product.variants[0]?.sku ?? "No SKU";
}

export function SuperDealsManager({ products }: { products: AdminProduct[] }) {
  const [selectedProductIds, setSelectedProductIds] = useState<string[]>([]);
  const [isSaving, setIsSaving] = useState(false);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);

  useEffect(() => {
    let active = true;

    async function loadSelectedDeals() {
      try {
        const response = await fetch("/api/uniforma/super-deals", {
          cache: "no-store"
        });
        if (!response.ok) return;

        const data = (await response.json()) as unknown;
        if (!active || !Array.isArray(data)) return;

        const ids = data
          .map((item) => (typeof (item as SuperDealProduct | null)?.id === "string" ? (item as SuperDealProduct).id : null))
          .filter((value): value is string => Boolean(value));

        setSelectedProductIds(ids);
      } catch {
        if (active) {
          setSelectedProductIds([]);
        }
      }
    }

    loadSelectedDeals();

    return () => {
      active = false;
    };
  }, []);

  async function saveSuperDeals() {
    setIsSaving(true);
    setStatusMessage(null);

    try {
      const response = await fetch("/api/uniforma/admin/super-deals", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(selectedProductIds)
      });

      if (!response.ok) {
        throw new Error("Failed to save super deals.");
      }

      setStatusMessage("Super deals saved.");
    } catch (error) {
      setStatusMessage(error instanceof Error ? error.message : "Failed to save super deals.");
    } finally {
      setIsSaving(false);
    }
  }

  function toggleProduct(productId: string) {
    setStatusMessage(null);
    setSelectedProductIds((current) =>
      current.includes(productId)
        ? current.filter((id) => id !== productId)
        : [...current, productId]
    );
  }

  if (products.length === 0) {
    return <EmptyState title="No products found" description="Sync products before creating super deals." />;
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <p className="text-sm text-slate-500">
            {selectedProductIds.length} selected
          </p>
          {statusMessage ? <p className="mt-1 text-sm text-slate-600">{statusMessage}</p> : null}
        </div>
        <button
          className="rounded-full bg-ink px-5 py-2 text-sm font-medium text-white disabled:cursor-not-allowed disabled:opacity-60"
          disabled={isSaving}
          onClick={saveSuperDeals}
          type="button"
        >
          {isSaving ? "Saving..." : "Save super deals"}
        </button>
      </div>

      <div className="overflow-hidden rounded-3xl bg-white shadow-panel">
        <table className="min-w-full divide-y divide-slate-200 text-sm">
          <thead className="bg-slate-50">
            <tr>
              <th className="px-4 py-3 text-left font-semibold text-slate-600">Product</th>
              <th className="px-4 py-3 text-left font-semibold text-slate-600">Variants</th>
              <th className="px-4 py-3 text-left font-semibold text-slate-600">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {products.map((product) => {
              const isSelected = selectedProductIds.includes(product.id);

              return (
                <tr key={product.id} className="hover:bg-slate-50/80">
                  <td className="px-4 py-4">
                    <p className="font-semibold text-ink">{product.name}</p>
                    <p className="mt-1 text-xs uppercase tracking-[0.16em] text-slate-500">
                      {product.external_id}
                    </p>
                  </td>
                  <td className="px-4 py-4 text-slate-600">
                    <p>{product.variants.length} variants</p>
                    <p className="text-xs text-slate-400">{getPrimarySku(product)}</p>
                  </td>
                  <td className="px-4 py-4">
                    <button
                      className={
                        isSelected
                          ? "rounded-full border border-slate-300 px-4 py-2 font-medium text-slate-700"
                          : "rounded-full bg-ink px-4 py-2 font-medium text-white"
                      }
                      onClick={() => toggleProduct(product.id)}
                      type="button"
                    >
                      {isSelected ? "ADDED" : "ADD"}
                    </button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

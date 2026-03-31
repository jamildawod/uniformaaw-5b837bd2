import { SuperDealsManager } from "@/components/admin/super-deals-manager";
import { ErrorState } from "@/components/ui/error-state";
import { Panel } from "@/components/ui/panel";
import { fetchAdminProducts } from "@/lib/api/server";

export default async function AdminSuperDealsPage() {
  try {
    const products = await fetchAdminProducts({
      page: 1,
      pageSize: 200,
      isActive: "all",
      deleted: "all",
      hasOverride: "all"
    });

    return (
      <div className="space-y-6">
        <Panel>
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-steel">Campaigns</p>
            <h2 className="mt-1 text-2xl font-semibold text-ink">Super Deals</h2>
            <p className="mt-2 text-sm text-slate-600">
              Select products to publish on the storefront super deals page.
            </p>
          </div>
        </Panel>
        <SuperDealsManager products={products} />
      </div>
    );
  } catch (error) {
    return (
      <ErrorState
        title="Failed to load super deals"
        message={error instanceof Error ? error.message : "Unknown error"}
      />
    );
  }
}
